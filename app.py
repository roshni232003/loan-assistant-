import streamlit as st
from openai import OpenAI
from fpdf import FPDF
import random, string, io
from datetime import datetime, timedelta

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="SVU Finance – AI Loan Assistant",
    page_icon="🏦",
    layout="centered"
)

# ── OpenAI client (key from Streamlit secrets) ───────────────
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }

.header {
    background: linear-gradient(135deg, #0d47a1 0%, #1976d2 100%);
    color: white; padding: 24px 32px; border-radius: 16px;
    text-align: center; margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(13,71,161,0.3);
}
.header h1 { margin:0; font-size:1.8rem; font-weight:700; }
.header p  { margin:6px 0 0; opacity:0.85; font-size:0.95rem; }

.user-msg {
    background: #0d47a1; color: white;
    padding: 12px 18px; border-radius: 18px 18px 4px 18px;
    margin: 6px 0 6px auto; max-width: 78%;
    font-size: 0.95rem; width: fit-content; margin-left: auto;
}
.bot-msg {
    background: #f0f7ff; color: #1a1a2e;
    padding: 14px 18px; border-radius: 18px 18px 18px 4px;
    margin: 6px 0; max-width: 85%;
    border-left: 4px solid #0d47a1;
    font-size: 0.95rem; white-space: pre-wrap;
}
.stage-pill {
    display:inline-block; background:#e3f2fd; color:#0d47a1;
    padding: 4px 14px; border-radius: 20px;
    font-size: 0.8rem; font-weight: 600; margin-bottom: 8px;
}
.approved-banner {
    background: linear-gradient(135deg,#1b5e20,#2e7d32);
    color:white; padding:16px; border-radius:12px;
    text-align:center; font-size:1.1rem; font-weight:700;
    margin: 10px 0;
}
.rejected-banner {
    background: linear-gradient(135deg,#b71c1c,#c62828);
    color:white; padding:16px; border-radius:12px;
    text-align:center; font-size:1.1rem; font-weight:700;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ── System prompt (all 7 agents condensed into one smart prompt) ─
SYSTEM_PROMPT = """You are an AI Loan Assistant for SVU Finance (Swami Vivekananda University).
You act as 7 agents in one: Sales, Data Collector, KYC Verifier, Credit Analyst, Approval Officer, and Letter Generator.

CONVERSATION FLOW — follow this STRICTLY in order:

PHASE 1 — SALES (first message only):
Greet warmly. Introduce SVU Finance. Ask what type of loan they want (Personal/Home/Education/Business).
Briefly explain the chosen loan product. Ask if they want to proceed.

PHASE 2 — DATA COLLECTION:
Collect these fields ONE AT A TIME (ask one, wait for answer, then ask next):
1. Full Name
2. Mobile Number
3. Email Address
4. PAN Number (format: ABCDE1234F)
5. Aadhaar Number (12 digits)
6. Age
7. Employment Type (Salaried or Self-Employed)
8. Years Employed
9. Monthly Income (₹)
10. Number of existing loans
11. Loan Amount needed (₹)
12. Loan Tenure (months: 12/24/36/48/60)
13. Loan Purpose

After collecting ALL 13, show a summary table and ask for confirmation.

PHASE 3 — KYC VERIFICATION:
Validate: PAN must match format ABCDE1234F. Aadhaar must be 12 digits.
If valid: "✅ KYC Verified!" and proceed.
If invalid: ask them to re-enter.

PHASE 4 — CREDIT ASSESSMENT:
Compute credit score mentally:
- Base: 750
- Subtract: 150 if income < 20000, 30 per existing loan, 100 if age<22 or age>60
- Add: 5 per year employed
- Range: 300-900
Show: Credit Score, EMI estimate (loan_amount × 0.115/12 approx), Risk Grade.

PHASE 5 — APPROVAL DECISION:
APPROVE if: credit_score >= 650, income >= 20000, existing_loans <= 3, age 21-65, EMI <= 50% income.
Otherwise REJECT with specific reasons and improvement tips.

PHASE 6 — SANCTION LETTER (if approved):
Tell user their sanction letter is ready. Say "GENERATE_PDF" on a new line followed by a JSON block:
GENERATE_PDF
{"name":"...","loan_amount":...,"tenure":...,"income":...,"credit_score":...,"purpose":"...","emi":...}

IMPORTANT RULES:
- Be friendly, warm, professional. Use emojis moderately.
- Ask ONE question at a time. Never skip steps.
- Always validate inputs before moving on.
- If user asks unrelated questions, answer briefly then redirect to application.
- Do NOT make up data. Use exactly what user provides.
"""

# ── PDF Generator ────────────────────────────────────────────
def generate_pdf(data: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    # Header
    pdf.set_fill_color(13, 71, 161)
    pdf.rect(0, 0, 210, 32, "F")
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(0, 10)
    pdf.cell(210, 10, "SVU FINANCE — LOAN SANCTION LETTER", align="C")
    pdf.ln(30)

    ref = "SVU/LOAN/" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    today = datetime.today()
    expiry = today + timedelta(days=30)
    rate = 0.115 if data.get("credit_score", 700) >= 750 else 0.135

    pdf.set_text_color(60, 60, 60)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"Ref: {ref}    |    Date: {today.strftime('%d %B %Y')}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(13, 71, 161)
    pdf.cell(0, 8, f"To: {data.get('name','').upper()}", ln=True)
    pdf.ln(3)

    pdf.set_fill_color(227, 242, 253)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, f"  Subject: Loan Sanction — INR {float(data.get('loan_amount',0)):,.0f}", ln=True, fill=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 7,
        f"Dear {data.get('name','')},\n\n"
        "We are pleased to inform you that your Personal Loan application has been APPROVED. "
        "Details of the sanctioned loan are as follows:"
    )
    pdf.ln(5)

    rows = [
        ("Sanctioned Amount",   f"INR {float(data.get('loan_amount',0)):,.2f}"),
        ("Loan Tenure",         f"{data.get('tenure',12)} Months"),
        ("Interest Rate",       f"{rate*100:.1f}% p.a."),
        ("Monthly EMI",         f"INR {float(data.get('emi',0)):,.2f}"),
        ("Loan Purpose",        str(data.get('purpose',''))),
        ("Credit Score",        str(data.get('credit_score',''))),
        ("Processing Fee",      f"INR {float(data.get('loan_amount',0))*0.01:,.2f}"),
        ("Offer Valid Until",   expiry.strftime("%d %B %Y")),
    ]

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(13, 71, 161)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(95, 9, "  DETAIL", border=0, fill=True)
    pdf.cell(95, 9, "  VALUE",  border=0, fill=True, ln=True)

    pdf.set_font("Helvetica", "", 10)
    for i, (k, v) in enumerate(rows):
        pdf.set_fill_color(232, 240, 253) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(95, 9, f"  {k}", border=1, fill=(i%2==0))
        pdf.cell(95, 9, f"  {v}", border=1, fill=(i%2==0), ln=True)

    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(13, 71, 161)
    pdf.cell(0, 7, "Terms & Conditions:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)
    for t in [
        "1. This sanction is valid for 30 days.",
        "2. Disbursement subject to successful document verification.",
        "3. Prepayment allowed after 6 EMIs with 2% foreclosure charge.",
        "4. EMI via NACH auto-debit mandate.",
    ]:
        pdf.cell(0, 6, t, ln=True)

    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(13, 71, 161)
    pdf.cell(0, 7, "Authorised By:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 6, "Ms. Sangita Bose — Head, Credit Operations, SVU Finance", ln=True)

    pdf.ln(6)
    pdf.set_fill_color(232, 245, 233)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(27, 94, 32)
    pdf.cell(0, 12, "Congratulations! Your loan has been sanctioned.", align="C", fill=True, ln=True)

    return bytes(pdf.output())


# ── Session state init ────────────────────────────────────────
if "messages"    not in st.session_state: st.session_state.messages    = []
if "history"     not in st.session_state: st.session_state.history     = []
if "pdf_data"    not in st.session_state: st.session_state.pdf_data    = None
if "pdf_name"    not in st.session_state: st.session_state.pdf_name    = "sanction_letter.pdf"
if "started"     not in st.session_state: st.session_state.started     = False

# ── Header ───────────────────────────────────────────────────
st.markdown("""
<div class="header">
    <h1>🏦 SVU Finance — AI Loan Assistant</h1>
    <p>Swami Vivekananda University · Final Year Project · Agentic AI</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏦 SVU Finance")
    st.markdown("**AI Loan Assistant**")
    st.divider()
    st.markdown("**How it works:**")
    st.markdown("1. 👋 Greet & choose loan type")
    st.markdown("2. 📝 Answer 13 quick questions")
    st.markdown("3. 🔍 KYC auto-verified")
    st.markdown("4. 📊 AI credit check")
    st.markdown("5. ✅ Get instant decision")
    st.markdown("6. 📄 Download sanction letter")
    st.divider()

    if st.button("🔄 Start New Application", use_container_width=True):
        st.session_state.messages  = []
        st.session_state.history   = []
        st.session_state.pdf_data  = None
        st.session_state.started   = False
        st.rerun()

    if st.session_state.pdf_data:
        st.divider()
        st.success("📄 Sanction letter ready!")
        st.download_button(
            label    = "⬇️ Download PDF Letter",
            data     = st.session_state.pdf_data,
            file_name= st.session_state.pdf_name,
            mime     = "application/pdf",
            use_container_width=True,
        )

    st.divider()
    st.caption("Built with Streamlit + OpenAI\nSVU Final Year Project 2025")


# ── Auto-start greeting ───────────────────────────────────────
def get_ai_reply(user_msg: str) -> str:
    st.session_state.history.append({"role": "user", "content": user_msg})
    response = client.chat.completions.create(
        model    = "gpt-4o-mini",
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.history,
        temperature = 0.4,
    )
    reply = response.choices[0].message.content
    st.session_state.history.append({"role": "assistant", "content": reply})
    return reply


def process_reply(reply: str):
    """Check if reply contains PDF generation instruction."""
    if "GENERATE_PDF" in reply:
        parts    = reply.split("GENERATE_PDF")
        text_part = parts[0].strip()
        json_part = parts[1].strip() if len(parts) > 1 else "{}"

        import json, re
        try:
            json_match = re.search(r'\{.*\}', json_part, re.DOTALL)
            if json_match:
                pdf_data = json.loads(json_match.group())
                pdf_bytes = generate_pdf(pdf_data)
                name = pdf_data.get("name", "Customer").replace(" ", "_")
                st.session_state.pdf_data = pdf_bytes
                st.session_state.pdf_name = f"sanction_letter_{name}.pdf"
                return text_part + "\n\n📄 **Your sanction letter is ready! Download it from the sidebar ⬅️**"
        except Exception:
            pass
        return text_part
    return reply


if not st.session_state.started:
    with st.spinner("Loading your assistant..."):
        reply = get_ai_reply("hello, start the loan application")
        reply = process_reply(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.started = True


# ── Render chat messages ──────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-msg">👤 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        content = msg["content"]
        if "CONGRATULATIONS" in content.upper() or "APPROVED" in content.upper() and "sanctioned" in content.lower():
            st.markdown(f'<div class="approved-banner">🎉 LOAN APPROVED!</div>', unsafe_allow_html=True)
        elif "NOT APPROVED" in content.upper() or "REJECTED" in content.upper():
            st.markdown(f'<div class="rejected-banner">❌ Application Not Approved</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="bot-msg">🤖 {content}</div>', unsafe_allow_html=True)


# ── Input box ─────────────────────────────────────────────────
st.divider()
with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            "message", placeholder="Type your answer here...",
            label_visibility="collapsed"
        )
    with col2:
        send = st.form_submit_button("Send ➤", use_container_width=True)

    if send and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("AI is thinking..."):
            reply = get_ai_reply(user_input)
            reply = process_reply(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
