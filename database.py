"""
database.py — PostgreSQL connection + all table models
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/loan_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─────────────────────────────────────────────
#  TABLE: customers
# ─────────────────────────────────────────────
class Customer(Base):
    __tablename__ = "customers"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String(100))
    phone          = Column(String(20))
    email          = Column(String(100))
    pan_number     = Column(String(20))
    aadhaar_number = Column(String(20))
    monthly_income = Column(Float)
    employment_type = Column(String(50))   # salaried / self-employed
    loan_amount    = Column(Float)
    loan_tenure    = Column(Integer)       # months
    purpose        = Column(String(200))
    credit_score   = Column(Integer)
    status         = Column(String(50), default="pending")  # pending / approved / rejected
    rejection_reason = Column(Text, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────────
#  TABLE: conversations
# ─────────────────────────────────────────────
class Conversation(Base):
    __tablename__ = "conversations"

    id          = Column(Integer, primary_key=True, index=True)
    session_id  = Column(String(100), index=True)
    role        = Column(String(20))   # user / assistant
    message     = Column(Text)
    timestamp   = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
#  TABLE: loan_applications
# ─────────────────────────────────────────────
class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id              = Column(Integer, primary_key=True, index=True)
    customer_id     = Column(Integer)
    session_id      = Column(String(100))
    application_no  = Column(String(50), unique=True)
    status          = Column(String(50), default="in_progress")
    sanction_letter = Column(String(500), nullable=True)  # file path
    created_at      = Column(DateTime, default=datetime.utcnow)


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
    print("✅ All database tables created!")


def get_db():
    """FastAPI dependency — yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    create_tables()
