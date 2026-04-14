"""
===================  LAYER 5 — PII MASKING (Privacy Layer)  ===================
Removes or hides sensitive information before it reaches the user.
Covers: salary, compensation, email, phone, Aadhaar, PAN, credit cards,
SSN, bank accounts, IP addresses, and date-of-birth patterns.

Applied in TWO places:
  1. On retrieved context — BEFORE the LLM ever sees the data
  2. On LLM output     — BEFORE each chunk reaches the user's browser

Flow position: Secure Retrieval → [PII Masking] → LLM → [PII Masking] → User
================================================================================
"""

import re
from typing import List, Tuple


# ─── PII Patterns ─────────────────────────────────────────────
# Each entry: (human-readable label, compiled regex, replacement)

PII_PATTERNS: List[Tuple[str, re.Pattern, str]] = [

    # ── Financial / Salary ────────────────────────────────────

    # Salary / CTC / compensation amounts (₹ or Rs or INR or $ followed by numbers)
    (
        "Salary",
        re.compile(
            r"(?:salary|ctc|compensation|package|stipend|pay|income|earning|wage)"
            r"\s*(?:is|was|of|:|-|–|—)?\s*"
            r"(?:₹|Rs\.?|INR|USD|\$|EUR|€)?\s*"
            r"[\d,]+(?:\.\d{1,2})?"
            r"(?:\s*(?:lpa|lac|lakh|lakhs|cr|crore|k|per\s*(?:month|annum|year)))?",
            re.IGNORECASE,
        ),
        "[SALARY REDACTED]",
    ),

    # Standalone currency amounts that look like salary figures (₹5,00,000 etc.)
    (
        "Currency Amount",
        re.compile(
            r"(?:₹|Rs\.?|INR)\s*[\d,]{4,}(?:\.\d{1,2})?"
            r"(?:\s*(?:lpa|lac|lakh|lakhs|cr|crore|k|per\s*(?:month|annum|year)))?",
            re.IGNORECASE,
        ),
        "[AMOUNT REDACTED]",
    ),

    # ── Contact Information ───────────────────────────────────

    # Email addresses
    (
        "Email",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "[EMAIL REDACTED]",
    ),

    # Phone numbers (international & Indian formats)
    (
        "Phone",
        re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "[PHONE REDACTED]",
    ),

    # ── Indian Identity Documents ─────────────────────────────

    # Aadhaar numbers (India) — 12 digits in groups of 4
    (
        "Aadhaar",
        re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
        "[AADHAAR REDACTED]",
    ),

    # PAN numbers (India) — ABCDE1234F
    (
        "PAN",
        re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
        "[PAN REDACTED]",
    ),

    # ── Financial Instruments ─────────────────────────────────

    # Credit / Debit card numbers — 13-19 digits, possibly separated
    (
        "Credit Card",
        re.compile(r"\b(?:\d{4}[-\s]?){3,4}\d{1,4}\b"),
        "[CARD REDACTED]",
    ),

    # Bank account numbers (8-18 digit sequences labelled as account)
    (
        "Bank Account",
        re.compile(
            r"(?:account\s*(?:no|number|#|num)?\s*(?:is|:|-|–|—)?\s*)\d{8,18}\b",
            re.IGNORECASE,
        ),
        "[BANK ACCOUNT REDACTED]",
    ),

    # IFSC codes (Indian bank branch codes) — ABCD0123456
    (
        "IFSC",
        re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
        "[IFSC REDACTED]",
    ),

    # ── International IDs ─────────────────────────────────────

    # Social Security Numbers (US) — XXX-XX-XXXX
    (
        "SSN",
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "[SSN REDACTED]",
    ),

    # ── Network / Technical ───────────────────────────────────

    # IP Addresses (IPv4)
    (
        "IP Address",
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "[IP REDACTED]",
    ),

    # ── Personal Details ──────────────────────────────────────

    # Date of birth patterns (DOB: 01/01/1990, DOB - 1990-01-01, etc.)
    (
        "Date of Birth",
        re.compile(
            r"(?:d\.?o\.?b|date\s*of\s*birth)\s*(?:is|:|-|–|—)?\s*"
            r"\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}",
            re.IGNORECASE,
        ),
        "[DOB REDACTED]",
    ),
]

# Toggle PII masking on/off (useful for dev debugging)
PII_MASKING_ENABLED = True


def mask_pii(text: str) -> str:
    """
    Scan text for PII patterns and replace matches with redaction labels.

    This is the core privacy function. It removes or hides sensitive
    information including salary, email, phone, Aadhaar, PAN, bank
    accounts, and more.

    Args:
        text: Raw text to scan (retrieved context or LLM response chunk).

    Returns:
        The same text with PII patterns replaced by [REDACTED] labels.
    """
    if not PII_MASKING_ENABLED or not text:
        return text

    masked_text = text
    for label, pattern, replacement in PII_PATTERNS:
        matches = pattern.findall(masked_text)
        if matches:
            print(f"🛡️  PII Masking: Redacted {len(matches)} {label} occurrence(s)")
            masked_text = pattern.sub(replacement, masked_text)

    return masked_text


def mask_pii_in_context(context: str) -> str:
    """
    Apply PII masking to retrieved data BEFORE it enters the LLM.
    This prevents the LLM from ever seeing raw sensitive information
    in source documents — salary, emails, phones, etc. are stripped
    before the model processes them.
    """
    return mask_pii(context)
