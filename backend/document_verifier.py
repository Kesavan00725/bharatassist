from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

from pypdf import PdfReader


def extract_pdf_text(pdf_bytes: bytes, max_chars: int = 200_000) -> str:
    reader = PdfReader(pdf_bytes)
    parts: list[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if t:
            parts.append(t)
        if sum(len(x) for x in parts) > max_chars:
            break
    return "\n".join(parts)[:max_chars]


def keyword_presence(text: str, keywords: list[str]) -> dict[str, bool]:
    t = (text or "").lower()
    found: dict[str, bool] = {}
    for k in keywords:
        k_norm = str(k).strip().lower()
        if not k_norm:
            continue
        found[k] = bool(re.search(r"\b" + re.escape(k_norm) + r"\b", t))
    return found


def normalize_doc_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def compare_declared_to_required(declared: list[str], required: list[str]) -> list[str]:
    declared_set = {normalize_doc_name(x) for x in (declared or [])}
    missing: list[str] = []
    for r in required or []:
        if normalize_doc_name(r) not in declared_set:
            missing.append(r)
    return missing


# ============================================================================
# DOCUMENT VERIFICATION SYSTEM
# ============================================================================

@dataclass
class ExtractedFields:
    """Fields extracted from document."""
    name: Optional[str] = None
    income: Optional[int] = None
    certificate_number: Optional[str] = None
    issue_date: Optional[str] = None
    issuing_authority: Optional[str] = None
    document_type: Optional[str] = None
    raw_text: str = ""


@dataclass
class VerificationResult:
    """Document verification result."""
    document_type: str
    status: str  # "valid" | "suspicious" | "mismatch" | "invalid"
    confidence_score: int  # 0-100
    extracted_fields: dict[str, Any]
    issues: list[str]
    risk_level: str  # "low" | "medium" | "high"
    validation_details: dict[str, Any] = None


# ============================================================================
# DOCUMENT TYPE DETECTION
# ============================================================================

DOCUMENT_TYPE_KEYWORDS = {
    "income_certificate": [
        "income certificate",
        "income proof",
        "certificate of income",
        "annual income",
        "gross income",
        "per annum",
    ],
    "aadhaar": [
        "aadhaar",
        "uid",
        "unique identification",
        "12-digit",
        "aadhaar number",
    ],
    "caste_certificate": [
        "caste certificate",
        "cast certificate",
        "sc certificate",
        "st certificate",
        "obc certificate",
        "scheduled caste",
        "scheduled tribe",
        "other backward",
    ],
    "ration_card": [
        "ration card",
        "ration",
        "fcs",
        "public distribution",
        "pds",
    ],
    "land_record": [
        "land record",
        "title deed",
        "property document",
        "land certificate",
        "7-12",
        "8-a",
    ],
}


def detect_document_type(text: str) -> tuple[str, float]:
    """Detect document type from text.

    Returns: (document_type, confidence_0_to_1)
    """
    text_lower = (text or "").lower()
    scores = {}

    for doc_type, keywords in DOCUMENT_TYPE_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        scores[doc_type] = matches / len(keywords) if keywords else 0

    if not scores or max(scores.values()) == 0:
        return "unknown", 0.0

    best_type = max(scores, key=scores.get)
    confidence = scores[best_type]
    return best_type, confidence


# ============================================================================
# FIELD EXTRACTION PATTERNS
# ============================================================================

EXTRACTION_PATTERNS = {
    "name": [
        r"(?:name|applicant name|named|holder)[\s:]*([A-Z][a-zA-Z\s\'-]*)",
        r"^([A-Z][a-zA-Z\s\'-]{5,50})$",
    ],
    "income": [
        r"(?:annual income|gross income|income)[\s:]*(?:Rs\.?|INR)?[\s]*([0-9,]+)",
        r"(?:per annum|pa|yearly)[\s]*(?:Rs\.?|INR)?[\s]*([0-9,]+)",
        r"income[\s]*(?:is|being|of)?[\s]*(?:Rs\.?|INR)?[\s]*([0-9,]+)",
    ],
    "certificate_number": [
        r"(?:certificate no|cert\. no|number|id)[\s:]*([A-Z0-9\-/]{5,20})",
        r"(?:aadhaar|uid)[\s:]*([0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4})",
        r"(?:certificate number|ref|reference)[\s:]*([0-9]{6,12})",
    ],
    "issue_date": [
        r"(?:issued|date|on)[\s]*(?:on)?[\s:]*([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})",
        r"([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})",
    ],
    "issuing_authority": [
        r"(?:issued by|issuing authority|from)[\s:]*([A-Z\s&,\.]{10,60})",
        r"(?:government|gram|block|district)[\s]*(?:of)?[\s]*([A-Z][a-zA-Z\s,\.]{5,40})",
    ],
}


def extract_fields(text: str) -> ExtractedFields:
    """Extract fields from document text using regex patterns."""
    text_clean = (text or "").strip()
    fields = ExtractedFields(raw_text=text_clean)

    # Extract name
    if text_clean:
        for pattern in EXTRACTION_PATTERNS["name"]:
            match = re.search(pattern, text_clean, re.MULTILINE | re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 3:
                    fields.name = name
                    break

    # Extract income
    for pattern in EXTRACTION_PATTERNS["income"]:
        match = re.search(pattern, text_clean, re.MULTILINE | re.IGNORECASE)
        if match:
            income_str = match.group(1).replace(",", "")
            try:
                fields.income = int(income_str)
                break
            except ValueError:
                continue

    # Extract certificate number
    for pattern in EXTRACTION_PATTERNS["certificate_number"]:
        match = re.search(pattern, text_clean, re.MULTILINE | re.IGNORECASE)
        if match:
            cert_num = match.group(1).strip()
            if len(cert_num) >= 5:
                fields.certificate_number = cert_num
                break

    # Extract issue date
    for pattern in EXTRACTION_PATTERNS["issue_date"]:
        match = re.search(pattern, text_clean, re.MULTILINE | re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            if _validate_date(date_str):
                fields.issue_date = date_str
                break

    # Extract issuing authority
    for pattern in EXTRACTION_PATTERNS["issuing_authority"]:
        match = re.search(pattern, text_clean, re.MULTILINE | re.IGNORECASE)
        if match:
            authority = match.group(1).strip()
            if len(authority) > 3:
                fields.issuing_authority = authority
                break

    return fields


def _validate_date(date_str: str) -> bool:
    """Validate date format (DD/MM/YYYY or DD-MM-YYYY)."""
    pattern = r"^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$"
    return bool(re.match(pattern, date_str.strip()))


# ============================================================================
# VALIDATION RULES
# ============================================================================

def _get_required_fields(doc_type: str) -> list[str]:
    """Get required fields for document type."""
    requirements = {
        "income_certificate": ["income", "certificate_number", "issuing_authority"],
        "aadhaar": ["certificate_number", "name"],
        "caste_certificate": ["certificate_number", "issuing_authority", "issue_date"],
        "ration_card": ["name", "certificate_number"],
        "land_record": ["certificate_number", "issuing_authority"],
        "unknown": ["name", "certificate_number"],
    }
    return requirements.get(doc_type, requirements["unknown"])


def _validate_income_format(income: Optional[int]) -> tuple[bool, Optional[str]]:
    """Validate income value."""
    if income is None:
        return True, None
    if income < 0:
        return False, "Income cannot be negative"
    if income > 10_000_000:
        return False, "Income seems unreasonably high (>10M)"
    if income < 1000:
        return False, "Income seems too low (<1000)"
    return True, None


def _validate_certificate_number(cert_num: Optional[str], doc_type: str) -> tuple[bool, Optional[str]]:
    """Validate certificate number format."""
    if cert_num is None:
        return True, None

    if len(cert_num) < 5:
        return False, "Certificate number too short"

    if doc_type == "aadhaar" and not re.match(r"^\d{4}[\s-]?\d{4}[\s-]?\d{4}$", cert_num):
        return False, "Invalid Aadhaar format (expected 12 digits)"

    return True, None


def _validate_profile_match(fields: ExtractedFields, user_profile: Optional[dict[str, Any]]) -> tuple[bool, list[str]]:
    """Check if extracted fields match user profile."""
    issues = []
    matches = True

    if not user_profile:
        return True, issues

    # Check name similarity (if both present)
    if fields.name and user_profile.get("name"):
        user_name = user_profile["name"].lower().strip()
        ext_name = fields.name.lower().strip()

        # Simple similarity check: first word or initials match
        user_words = user_name.split()
        ext_words = ext_name.split()

        if user_words and ext_words:
            if user_words[0] != ext_words[0]:
                issues.append(f"Name mismatch: document has '{fields.name}', user profile has '{user_profile['name']}'")
                matches = False

    # Check income range (if both present)
    if fields.income and user_profile.get("income_inr"):
        user_income = user_profile["income_inr"]
        extracted_income = fields.income

        # Allow ±20% variance
        min_acceptable = user_income * 0.8
        max_acceptable = user_income * 1.2

        if not (min_acceptable <= extracted_income <= max_acceptable):
            issues.append(
                f"Income mismatch: document shows {extracted_income:,}, "
                f"user profile shows {user_income:,}"
            )
            matches = False

    return matches, issues


# ============================================================================
# CONFIDENCE SCORING
# ============================================================================

def _calculate_confidence(fields: ExtractedFields, doc_type: str, required_fields: list[str]) -> int:
    """Calculate confidence score (0-100)."""
    score = 0

    # Presence score (50 points)
    fields_present = sum([
        1 for field in required_fields
        if getattr(fields, field.lower()) is not None
    ])
    presence_score = (fields_present / len(required_fields) * 50) if required_fields else 0
    score += presence_score

    # Format validation score (30 points)
    format_valid = 0
    format_total = 0

    if fields.income is not None:
        format_total += 1
        is_valid, _ = _validate_income_format(fields.income)
        if is_valid:
            format_valid += 1

    if fields.certificate_number is not None:
        format_total += 1
        is_valid, _ = _validate_certificate_number(fields.certificate_number, doc_type)
        if is_valid:
            format_valid += 1

    if fields.issue_date is not None:
        format_total += 1
        if _validate_date(fields.issue_date):
            format_valid += 1

    if format_total > 0:
        format_score = (format_valid / format_total * 30)
        score += format_score

    # Text extraction quality (20 points)
    text_quality_score = 20 if len(fields.raw_text) > 100 else 10
    score += text_quality_score

    return int(score)


# ============================================================================
# RISK ASSESSMENT
# ============================================================================

def _assess_risk_level(issues: list[str], confidence: int, suspicious_indicators: list[str]) -> str:
    """Assess risk level based on issues and confidence."""
    if suspicious_indicators or confidence < 40:
        return "high"
    elif issues or confidence < 60:
        return "medium"
    else:
        return "low"


def _check_suspicious_indicators(text: str, fields: ExtractedFields) -> list[str]:
    """Check for suspicious patterns or indicators."""
    indicators = []
    text_lower = (text or "").lower()

    # Check for signs of tampering
    if "whiteout" in text_lower or "correction" in text_lower or "modified" in text_lower:
        indicators.append("Document appears to have corrections or modifications")

    # Check for photocopy indicators
    if "photocopy" in text_lower or "attested" not in text_lower and "original" in text_lower:
        indicators.append("Document may be a photocopy (verify with original)")

    # Check for expired certificate
    if fields.issue_date:
        # Very old dates might be suspicious
        year_match = re.search(r"(\d{4})", fields.issue_date)
        if year_match:
            year = int(year_match.group(1))
            if year < 2015:
                indicators.append(f"Certificate is from {year} (very old, may need renewal)")

    # Check for common fraud keywords
    fraud_keywords = ["fake", "dummy", "test", "sample"]
    for keyword in fraud_keywords:
        if keyword in text_lower:
            indicators.append(f"Suspicious keyword found: '{keyword}'")

    return indicators


# ============================================================================
# MAIN VERIFICATION FUNCTION
# ============================================================================

def verify_pdf_document(
    pdf_bytes: bytes,
    user_profile: Optional[dict[str, Any]] = None,
) -> VerificationResult:
    """Verify a PDF document comprehensively.

    Args:
        pdf_bytes: PDF file bytes
        user_profile: Optional user profile dict with name, income_inr, etc.

    Returns:
        VerificationResult with document_type, status, confidence, issues, risk_level
    """
    # Extract text
    try:
        text = extract_pdf_text(pdf_bytes)
    except Exception as e:
        return VerificationResult(
            document_type="unknown",
            status="invalid",
            confidence_score=0,
            extracted_fields={},
            issues=[f"Failed to extract PDF text: {type(e).__name__}"],
            risk_level="high",
        )

    # Detect document type
    doc_type, doc_confidence = detect_document_type(text)

    # Extract fields
    fields = extract_fields(text)

    # Get required fields for this document type
    required_fields = _get_required_fields(doc_type)

    # Validate individual fields
    validation_issues = []
    validation_details = {}

    if fields.income is not None:
        is_valid, issue = _validate_income_format(fields.income)
        validation_details["income_valid"] = is_valid
        if not is_valid:
            validation_issues.append(f"Income: {issue}")

    if fields.certificate_number is not None:
        is_valid, issue = _validate_certificate_number(fields.certificate_number, doc_type)
        validation_details["cert_num_valid"] = is_valid
        if not is_valid:
            validation_issues.append(f"Certificate number: {issue}")

    if fields.issue_date is not None:
        is_valid = _validate_date(fields.issue_date)
        validation_details["date_valid"] = is_valid
        if not is_valid:
            validation_issues.append(f"Issue date format invalid: {fields.issue_date}")

    # Check profile match
    profile_match, profile_issues = _validate_profile_match(fields, user_profile)
    validation_issues.extend(profile_issues)
    validation_details["profile_match"] = profile_match

    # Check for suspicious indicators
    suspicious = _check_suspicious_indicators(text, fields)
    validation_issues.extend(suspicious)

    # Calculate confidence score
    confidence = _calculate_confidence(fields, doc_type, required_fields)

    # Determine status
    missing_required = [f for f in required_fields if getattr(fields, f.lower()) is None]

    if suspicious:
        status = "suspicious"
    elif missing_required:
        status = "mismatch" if confidence > 50 else "invalid"
    elif not profile_match:
        status = "mismatch"
    elif confidence >= 80:
        status = "valid"
    elif confidence >= 60:
        status = "suspicious"
    else:
        status = "invalid"

    # Assess risk level
    risk_level = _assess_risk_level(validation_issues, confidence, suspicious)

    # Build extracted fields dict
    extracted_dict = {
        "name": fields.name,
        "income": fields.income,
        "certificate_number": fields.certificate_number,
        "issue_date": fields.issue_date,
        "issuing_authority": fields.issuing_authority,
    }

    return VerificationResult(
        document_type=doc_type,
        status=status,
        confidence_score=confidence,
        extracted_fields=extracted_dict,
        issues=validation_issues,
        risk_level=risk_level,
        validation_details=validation_details,
    )

