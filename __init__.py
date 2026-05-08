"""
agents/verification_agent.py — Validates KYC using mock CRM + OCR
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ocr_utils import mock_kyc_verify


class VerificationAgent:
    """
    Verifies the customer's KYC documents.
    In production: connects to CKYC / DigiLocker / Aadhaar APIs.
    For this project: uses a mock CRM verification.
    """

    def verify(self, pan: str, aadhaar: str, name: str) -> dict:
        """
        Run KYC verification and return a result dictionary.
        """
        print(f"\n🔍 [VerificationAgent] Verifying KYC for {name}...")
        result = mock_kyc_verify(pan, aadhaar, name)

        # Log the verification
        print(f"   PAN Valid:     {result['pan_valid']}")
        print(f"   Aadhaar Valid: {result['aadhaar_valid']}")
        print(f"   KYC Status:    {result['message']}")

        return result

    def verify_from_file(self, image_path: str, expected_pan: str, expected_aadhaar: str) -> dict:
        """
        (Optional) Run OCR on an uploaded image to verify document details.
        """
        from utils.ocr_utils import extract_text_from_image, verify_pan, verify_aadhaar

        text = extract_text_from_image(image_path)
        if not text or "OCR Error" in text:
            return {
                "kyc_passed": False,
                "message": "Could not read document image. Please upload a clearer image."
            }

        pan_ok     = verify_pan(text, expected_pan)
        aadhaar_ok = verify_aadhaar(text, expected_aadhaar[-4:])

        return {
            "pan_valid":     pan_ok,
            "aadhaar_valid": aadhaar_ok,
            "kyc_passed":    pan_ok and aadhaar_ok,
            "message":       "KYC Verified ✅" if (pan_ok and aadhaar_ok) else "KYC Failed ❌",
        }

    def format_result_message(self, result: dict) -> str:
        if result["kyc_passed"]:
            return (
                "✅ **KYC Verification Successful!**\n"
                "Your PAN and Aadhaar have been verified. "
                "Proceeding to credit assessment..."
            )
        else:
            issues = []
            if not result.get("pan_valid"):
                issues.append("PAN number is invalid")
            if not result.get("aadhaar_valid"):
                issues.append("Aadhaar number is invalid")
            return (
                "❌ **KYC Verification Failed**\n"
                f"Issues found: {', '.join(issues)}.\n"
                "Please double-check your documents and try again."
            )
