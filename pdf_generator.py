"""
utils/ocr_utils.py — Extract text from uploaded ID/income documents using Tesseract OCR
"""
import pytesseract
from PIL import Image
import re
import os


def extract_text_from_image(image_path: str) -> str:
    """
    Read an image file and return the extracted text.
    Supports: PNG, JPG, JPEG, TIFF, BMP
    """
    if not os.path.exists(image_path):
        return ""
    try:
        img  = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang="eng")
        return text.strip()
    except Exception as e:
        return f"OCR Error: {str(e)}"


def verify_pan(text: str, expected_pan: str) -> bool:
    """Check if the PAN number appears in the extracted OCR text."""
    pan_pattern = r"[A-Z]{5}[0-9]{4}[A-Z]{1}"
    found = re.findall(pan_pattern, text.upper())
    return expected_pan.upper() in found


def verify_aadhaar(text: str, expected_last4: str) -> bool:
    """Check if Aadhaar last-4 digits appear in the extracted OCR text."""
    aadhaar_pattern = r"\b\d{4}\b"
    found = re.findall(aadhaar_pattern, text)
    return expected_last4 in found


def extract_name_from_pan(text: str) -> str:
    """
    Attempt to extract the name printed on a PAN card.
    (Heuristic: line after 'NAME' keyword)
    """
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "NAME" in line.upper() and i + 1 < len(lines):
            candidate = lines[i + 1].strip()
            if candidate and len(candidate) > 2:
                return candidate
    return "Unknown"


def mock_kyc_verify(pan: str, aadhaar: str, name: str) -> dict:
    """
    Mock CRM/KYC verification — simulates calling a real KYC API.
    In production, replace with actual CKYC / Aadhaar API call.
    """
    # Simulate: PAN must be 10 chars, Aadhaar must be 12 digits
    pan_valid     = bool(re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan.strip().upper()))
    aadhaar_valid = bool(re.match(r"^\d{12}$", aadhaar.replace(" ", "")))

    return {
        "pan_valid":     pan_valid,
        "aadhaar_valid": aadhaar_valid,
        "name_match":    True,               # simplified
        "kyc_passed":    pan_valid and aadhaar_valid,
        "message":       "KYC Verified ✅" if pan_valid and aadhaar_valid else "KYC Failed ❌ — Invalid document(s)",
    }
