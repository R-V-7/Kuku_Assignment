"""Layer 1: Pre-Ingestion Guardrails - Regex PII Redactor."""

import re


def redact_pii(text: str) -> tuple[str, list[dict[str, str]]]:
    """Mask sensitive Indian personal identifiers (Aadhaar, PAN, phone, email)

    before sending user-submitted text to any external LLM provider.
    """
    redacted = text
    log: list[dict[str, str]] = []

    # 1. Aadhaar Card Pattern: 12 digits (with optional spaces/dashes)
    aadhaar_pattern = r"\b[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b"
    for match in re.finditer(aadhaar_pattern, redacted):
        val = match.group(0)
        log.append({"type": "Aadhaar Card", "original": val[:4] + " **** " + val[-4:]})
    redacted = re.sub(aadhaar_pattern, "<AADHAAR_REDACTED>", redacted)

    # 2. PAN Card Pattern: 5 uppercase letters + 4 digits + 1 uppercase letter
    pan_pattern = r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"
    for match in re.finditer(pan_pattern, redacted, re.IGNORECASE):
        val = match.group(0).upper()
        log.append({"type": "PAN Card", "original": val[:2] + "*****" + val[-2:]})
    redacted = re.sub(pan_pattern, "<PAN_REDACTED>", redacted, flags=re.IGNORECASE)

    # 3. Indian Phone Numbers: 10 digits starting with 6-9, with optional +91/0 prefix
    phone_pattern = r"(?:\+?91[\-\s]?)?[6-9]\d{9}\b"
    for match in re.finditer(phone_pattern, redacted):
        val = match.group(0)
        log.append({"type": "Phone Number", "original": val[:4] + "***" + val[-3:]})
    redacted = re.sub(phone_pattern, "<PHONE_REDACTED>", redacted)

    # 4. Email Addresses
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    for match in re.finditer(email_pattern, redacted):
        val = match.group(0)
        log.append({"type": "Email Address", "original": val.split("@")[0][:2] + "***@" + val.split("@")[1]})
    redacted = re.sub(email_pattern, "<EMAIL_REDACTED>", redacted)

    return redacted, log

