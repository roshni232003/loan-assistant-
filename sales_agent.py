"""
agents/credit_agent.py — Fetches/computes credit score & runs eligibility check
"""
import joblib
import numpy as np
import os
import random


class CreditRiskAgent:
    """
    Uses the trained XGBoost model to:
    1. Simulate a credit score
    2. Predict loan approval probability
    3. Return eligibility verdict
    """

    def __init__(self):
        model_path    = os.path.join(os.path.dirname(__file__), "..", "ml", "credit_model.pkl")
        features_path = os.path.join(os.path.dirname(__file__), "..", "ml", "feature_names.pkl")

        self.model    = None
        self.features = None

        if os.path.exists(model_path):
            self.model    = joblib.load(model_path)
            self.features = joblib.load(features_path)
            print("✅ [CreditRiskAgent] ML model loaded.")
        else:
            print("⚠️  [CreditRiskAgent] Model not found. Run ml/train_model.py first. Using rule-based fallback.")

    def simulate_credit_score(self, monthly_income: float, existing_loans: int,
                               employment_years: int, past_defaults: int = 0) -> int:
        """
        Simulate a credit score (300–900) based on customer profile.
        In production, this calls CIBIL / Experian API.
        """
        base = 750
        score = (
            base
            - past_defaults    * 150
            - existing_loans   * 25
            + employment_years * 4
            + min(monthly_income / 5000, 60)
            + random.randint(-20, 20)       # small random noise
        )
        return int(max(300, min(900, score)))

    def assess_risk(self, customer_data: dict) -> dict:
        """
        Full credit risk assessment.
        Returns: credit_score, approval_probability, decision, reasons
        """
        income         = float(customer_data.get("monthly_income", 0))
        loan_amount    = float(customer_data.get("loan_amount", 0))
        tenure         = int(customer_data.get("loan_tenure", 12))
        age            = int(customer_data.get("age", 30))
        existing_loans = int(customer_data.get("existing_loans", 0))
        emp_years      = int(customer_data.get("employment_years", 0))
        emp_type       = customer_data.get("employment_type", "salaried")
        emp_type_enc   = 0 if emp_type == "salaried" else 1

        # Step 1: Simulate credit score
        credit_score = self.simulate_credit_score(income, existing_loans, emp_years)

        # Step 2: ML prediction
        if self.model:
            features_vec = np.array([[
                income,
                loan_amount,
                tenure,
                age,
                existing_loans,
                emp_years,
                emp_type_enc,
                0,                          # past_defaults (0 = not known)
                0.4,                        # credit_utilization (assume moderate)
                credit_score
            ]])
            prob = float(self.model.predict_proba(features_vec)[0][1])
        else:
            # Rule-based fallback
            prob = 0.8 if credit_score >= 700 and income >= 25000 else 0.3

        # Step 3: EMI affordability check
        monthly_rate = 0.115 / 12
        emi = loan_amount * monthly_rate * (1 + monthly_rate) ** tenure / \
              ((1 + monthly_rate) ** tenure - 1)
        emi_to_income_ratio = emi / income if income > 0 else 1

        # Step 4: Build rejection reasons
        reasons = []
        if credit_score < 650:
            reasons.append(f"Credit score ({credit_score}) is below minimum threshold of 650")
        if income < 20000:
            reasons.append(f"Monthly income (₹{income:,.0f}) is below minimum ₹20,000")
        if emi_to_income_ratio > 0.5:
            reasons.append(f"EMI (₹{emi:,.0f}) exceeds 50% of your monthly income")
        if existing_loans >= 3:
            reasons.append(f"Too many existing loans ({existing_loans})")
        if age < 21 or age > 65:
            reasons.append(f"Age ({age}) outside eligible range of 21–65 years")

        approved = len(reasons) == 0 and prob >= 0.55

        return {
            "credit_score":         credit_score,
            "approval_probability": round(prob * 100, 1),
            "monthly_emi":          round(emi, 2),
            "emi_income_ratio":     round(emi_to_income_ratio * 100, 1),
            "approved":             approved,
            "rejection_reasons":    reasons,
            "risk_grade":           self._grade(credit_score),
        }

    def _grade(self, score: int) -> str:
        if score >= 800: return "Excellent (A+)"
        if score >= 750: return "Very Good (A)"
        if score >= 700: return "Good (B+)"
        if score >= 650: return "Fair (B)"
        if score >= 600: return "Poor (C)"
        return "Very Poor (D)"

    def format_report(self, result: dict) -> str:
        status = "✅ APPROVED" if result["approved"] else "❌ NOT APPROVED"
        report = (
            f"📊 **Credit Risk Assessment Report**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏅 Credit Score:          {result['credit_score']} — {result['risk_grade']}\n"
            f"📈 Approval Probability:  {result['approval_probability']}%\n"
            f"💸 Monthly EMI:           ₹{result['monthly_emi']:,}\n"
            f"📉 EMI/Income Ratio:      {result['emi_income_ratio']}%\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔰 Decision: {status}\n"
        )
        if result["rejection_reasons"]:
            report += "\n⚠️  Reasons:\n"
            for r in result["rejection_reasons"]:
                report += f"   • {r}\n"
        return report
