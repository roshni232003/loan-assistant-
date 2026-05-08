"""
main.py — FastAPI application: All API endpoints
Run with: uvicorn main:app --reload
"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import os
import shutil
from datetime import datetime

from database import get_db, create_tables, Conversation, Customer, LoanApplication
from agents.master_agent import MasterAgent

# ─────────────────────────────────────────────
#  App Setup
# ─────────────────────────────────────────────
app = FastAPI(
    title="SVU Finance — AI Loan Assistant API",
    description="Agentic AI-Powered Conversational Loan Assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session store: session_id → MasterAgent instance
SESSIONS: dict[str, MasterAgent] = {}

os.makedirs("sanction_letters", exist_ok=True)
os.makedirs("uploads", exist_ok=True)


# ─────────────────────────────────────────────
#  Request/Response Models
# ─────────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    stage: str
    is_complete: bool

class SessionResponse(BaseModel):
    session_id: str
    message: str

class StatusResponse(BaseModel):
    status: str
    version: str
    sessions_active: int


# ─────────────────────────────────────────────
#  Startup
# ─────────────────────────────────────────────
@app.on_event("startup")
def startup_event():
    try:
        create_tables()
        print("✅ Database ready")
    except Exception as e:
        print(f"⚠️  DB connection failed (continuing without DB): {e}")


# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────

@app.get("/", response_model=StatusResponse)
def root():
    """Health check endpoint."""
    return {
        "status": "✅ SVU Finance AI Loan Assistant is running!",
        "version": "1.0.0",
        "sessions_active": len(SESSIONS),
    }


@app.post("/session/new", response_model=SessionResponse)
def new_session():
    """Create a new conversation session. Returns a unique session_id."""
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = MasterAgent(session_id=session_id)
    return {"session_id": session_id, "message": "New session created. Send your first message to /chat!"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main chat endpoint.
    - Creates a new session if session_id not provided
    - Routes message to MasterAgent
    - Saves conversation to database
    """
    # Get or create session
    session_id = request.session_id
    if not session_id or session_id not in SESSIONS:
        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = MasterAgent(session_id=session_id)

    agent = SESSIONS[session_id]

    # Get reply
    reply = agent.chat(request.message)

    # Save to DB (optional — won't crash if DB is unavailable)
    try:
        db.add(Conversation(session_id=session_id, role="user",      message=request.message))
        db.add(Conversation(session_id=session_id, role="assistant", message=reply))
        db.commit()
    except Exception:
        pass

    is_complete = agent.stage in ("done", "letter")

    return {
        "session_id": session_id,
        "reply":       reply,
        "stage":       agent.stage,
        "is_complete": is_complete,
    }


@app.get("/chat/history/{session_id}")
def get_history(session_id: str):
    """Return the full conversation history for a session."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "history": SESSIONS[session_id].history}


@app.post("/session/{session_id}/reset")
def reset_session(session_id: str):
    """Reset a session (start fresh conversation)."""
    if session_id in SESSIONS:
        SESSIONS[session_id].reset()
        return {"message": "Session reset successfully"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/session/{session_id}/status")
def session_status(session_id: str):
    """Get the current stage and customer data for a session."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    agent = SESSIONS[session_id]
    data  = agent.worker_agent.data.model_dump()
    return {
        "session_id":    session_id,
        "stage":         agent.stage,
        "customer_data": data,
        "kyc_result":    agent.kyc_result,
        "credit_result": agent.credit_result,
        "approval":      agent.approval_result,
    }


@app.post("/upload/document/{session_id}")
async def upload_document(session_id: str, file: UploadFile = File(...)):
    """
    Upload a KYC document image (PAN card / Aadhaar) for OCR verification.
    """
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    filename = f"{session_id}_{file.filename}"
    filepath = os.path.join("uploads", filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    agent = SESSIONS[session_id]
    data  = agent.worker_agent.data

    kyc_result = agent.verif_agent.verify_from_file(
        image_path       = filepath,
        expected_pan     = data.pan_number or "",
        expected_aadhaar = data.aadhaar_number or "",
    )

    return {"filename": filename, "kyc_result": kyc_result}


@app.get("/download/sanction/{session_id}")
def download_sanction_letter(session_id: str):
    """Download the generated sanction letter PDF."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    agent = SESSIONS[session_id]
    name  = agent.worker_agent.data.name or "Customer"
    today = datetime.today().strftime("%Y%m%d")
    filename = f"sanction_{name.replace(' ', '_')}_{today}.pdf"
    filepath  = os.path.join("sanction_letters", filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Sanction letter not yet generated")

    return FileResponse(filepath, media_type="application/pdf", filename=filename)


@app.get("/admin/sessions")
def list_sessions():
    """Admin: list all active sessions."""
    return {
        "total": len(SESSIONS),
        "sessions": [
            {"session_id": sid, "stage": agent.stage}
            for sid, agent in SESSIONS.items()
        ]
    }


@app.delete("/admin/sessions/clear")
def clear_sessions():
    """Admin: clear all sessions."""
    SESSIONS.clear()
    return {"message": "All sessions cleared"}
