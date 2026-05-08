"""
agents/letter_agent.py — Triggers PDF sanction letter generation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.pdf_generator import generate_sanction_letter


class LetterAgent:
    """
    Generates the official PDF sanction letter once a loan is approved.
    """

    def generate(self, customer_data: dict, credit_result: dict) -> dict:
        """
        Generate the sanction letter PDF.
        Returns: file_path, success, message
        """
        try:
            filepath = generate_sanction_letter(
                customer_name  = customer_data.get("name", "Customer"),
                loan_amount    = float(customer_data.get("loan_amount", 0)),
                loan_tenure    = int(customer_data.get("loan_tenure", 12)),
                monthly_income = float(customer_data.get("monthly_income", 0)),
                credit_score   = credit_result.get("credit_score", 700),
                purpose        = customer_data.get("purpose", "Personal Use"),
                output_dir     = "sanction_letters",
            )

            name = customer_data.get("name", "Applicant")
            return {
                "success":   True,
                "file_path": filepath,
                "message": (
                    f"📄 **Sanction Letter Generated!**\n\n"
                    f"Dear {name}, your official loan sanction letter is ready.\n\n"
                    f"📁 File: `{os.path.basename(filepath)}`\n\n"
                    f"**Next Steps:**\n"
                    f"   1️⃣  Download your sanction letter\n"
                    f"   2️⃣  Sign and upload the acceptance form\n"
                    f"   3️⃣  Set up your NACH mandate for EMI auto-debit\n"
                    f"   4️⃣  Loan amount will be credited within 48 hours! 🚀\n\n"
                    f"Thank you for choosing SVU Finance! 🏦"
                ),
            }

        except Exception as e:
            return {
                "success":   False,
                "file_path": None,
                "message":   f"❌ Could not generate sanction letter: {str(e)}. Please contact support.",
            }
