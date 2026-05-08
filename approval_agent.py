"""
agents/worker_agent.py — Collects all required customer data
"""
from pydantic import BaseModel
from typing import Optional


class CustomerData(BaseModel):
    name:             Optional[str]   = None
    phone:            Optional[str]   = None
    email:            Optional[str]   = None
    pan_number:       Optional[str]   = None
    aadhaar_number:   Optional[str]   = None
    monthly_income:   Optional[float] = None
    employment_type:  Optional[str]   = None   # salaried / self-employed
    employment_years: Optional[int]   = None
    existing_loans:   Optional[int]   = 0
    loan_amount:      Optional[float] = None
    loan_tenure:      Optional[int]   = None   # months
    purpose:          Optional[str]   = None
    age:              Optional[int]   = None


# ─────────────────────────────────────────────
#  Fields the agent must collect (in order)
# ─────────────────────────────────────────────
REQUIRED_FIELDS = [
    ("name",             "What is your full name?"),
    ("phone",            "What is your mobile number?"),
    ("email",            "What is your email address?"),
    ("pan_number",       "Please share your PAN number (e.g., ABCDE1234F):"),
    ("aadhaar_number",   "Please share your 12-digit Aadhaar number:"),
    ("age",              "What is your age?"),
    ("employment_type",  "Are you Salaried or Self-Employed?"),
    ("employment_years", "How many years have you been employed?"),
    ("monthly_income",   "What is your monthly take-home income (in ₹)?"),
    ("existing_loans",   "How many active loans do you currently have?"),
    ("loan_amount",      "How much loan amount do you need (in ₹)?"),
    ("loan_tenure",      "For how many months would you like to repay? (e.g., 12, 24, 36, 48, 60)"),
    ("purpose",          "What is the purpose of this loan?"),
]


class WorkerAgent:
    """
    Guides the user through data collection step by step.
    Tracks which fields are filled and which are still pending.
    """

    def __init__(self):
        self.data    = CustomerData()
        self.pending = list(REQUIRED_FIELDS)   # fields still needed

    def is_complete(self) -> bool:
        return len(self.pending) == 0

    def next_question(self) -> str:
        """Return the next question to ask the user."""
        if self.pending:
            return self.pending[0][1]
        return "All information collected! ✅"

    def fill_field(self, value: str) -> str:
        """
        Fill in the next pending field with the user's answer.
        Returns a confirmation or error message.
        """
        if not self.pending:
            return "All fields already filled."

        field_name, question = self.pending[0]

        try:
            parsed = self._parse(field_name, value.strip())
            setattr(self.data, field_name, parsed)
            self.pending.pop(0)

            if self.pending:
                return f"Got it! ✅ Next — {self.pending[0][1]}"
            else:
                return "All information collected! Moving to verification... 🔍"

        except ValueError as e:
            return f"❌ Invalid input — {str(e)}. Please try again: {question}"

    def _parse(self, field: str, value: str):
        """Type-cast the raw string value to the correct Python type."""
        if field in ("monthly_income", "loan_amount"):
            cleaned = value.replace(",", "").replace("₹", "").replace(" ", "")
            return float(cleaned)
        elif field in ("age", "employment_years", "existing_loans", "loan_tenure"):
            return int(value)
        elif field == "employment_type":
            v = value.lower()
            if "salar" in v:
                return "salaried"
            elif "self" in v or "business" in v:
                return "self-employed"
            else:
                raise ValueError("Please say 'Salaried' or 'Self-Employed'")
        elif field == "pan_number":
            import re
            if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", value.upper()):
                raise ValueError("PAN must be in format ABCDE1234F")
            return value.upper()
        elif field == "aadhaar_number":
            cleaned = value.replace(" ", "")
            if len(cleaned) != 12 or not cleaned.isdigit():
                raise ValueError("Aadhaar must be 12 digits")
            return cleaned
        else:
            return value

    def get_summary(self) -> str:
        """Return a readable summary of collected data."""
        d = self.data
        return (
            f"📋 **Application Summary**\n"
            f"👤 Name:             {d.name}\n"
            f"📞 Phone:            {d.phone}\n"
            f"📧 Email:            {d.email}\n"
            f"🪪 PAN:              {d.pan_number}\n"
            f"🔑 Aadhaar (last4):  {str(d.aadhaar_number)[-4:] if d.aadhaar_number else 'N/A'}\n"
            f"🎂 Age:              {d.age}\n"
            f"💼 Employment:       {d.employment_type} ({d.employment_years} yrs)\n"
            f"💰 Monthly Income:   ₹{d.monthly_income:,.0f}\n"
            f"🏦 Existing Loans:   {d.existing_loans}\n"
            f"💳 Loan Requested:   ₹{d.loan_amount:,.0f} for {d.loan_tenure} months\n"
            f"📝 Purpose:          {d.purpose}"
        )
