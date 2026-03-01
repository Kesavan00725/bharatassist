# Document Verification API Documentation

## Overview

BharatAssist provides comprehensive PDF document verification with type detection, field extraction, and validation. The system is rule-based (no machine learning) and uses regex patterns for field extraction and keyword matching for document detection.

## API Endpoints

### 1. POST /document-verify (Comprehensive Verification)

Performs full document verification with type detection, field extraction, validation, and risk assessment.

**URL:** `POST /document-verify`

**Content-Type:** `multipart/form-data`

**Parameters:**

- `file` (required): PDF file (multipart upload)
- `user_profile` (optional): JSON string with user data for validation

**User Profile Fields (Optional):**

```json
{
  "name": "John Doe",
  "income_inr": 150000,
  "category": "general",
  "state": "maharashtra"
}
```

**Response:**

```json
{
  "document_type": "income_certificate",
  "status": "valid",
  "confidence_score": 85,
  "extracted_fields": {
    "name": "John Doe",
    "income": 150000,
    "certificate_number": "IC-2024-001",
    "issue_date": "01/15/2024",
    "issuing_authority": "Revenue Department, Maharashtra"
  },
  "issues": [],
  "risk_level": "low",
  "validation_details": {
    "income_valid": true,
    "cert_num_valid": true,
    "date_valid": true,
    "profile_match": true
  }
}
```

### 2. POST /verify-pdf (Scheme-Specific Verification)

Verifies documents against specific government scheme requirements.

**URL:** `POST /verify-pdf`

**Content-Type:** `multipart/form-data`

**Parameters:**

- `req_json` (required): JSON string with VerifyRequest
- `file` (required): PDF file (multipart upload)

**Request Format:**

```json
{
  "scheme_id": "pm-kisan",
  "declared_documents": ["Aadhaar", "Land Records", "Bank Passbook"]
}
```

**Response:**

```json
{
  "scheme_id": "pm-kisan",
  "scheme_name": "PM-KISAN",
  "required_documents": ["Aadhaar", "Land Records", "Bank Details"],
  "declared_documents": ["Aadhaar", "Land Records", "Bank Passbook"],
  "missing_declared": [],
  "pdf_found_keywords": {
    "Aadhaar": true,
    "Land Records": true,
    "Bank Details": true
  },
  "verdict": "Looks okay based on declared docs (and PDF keyword scan)."
}
```

## Document Type Detection

The system automatically detects the following document types based on keyword matching:

### Supported Document Types

| Type                   | Keywords                                                                                                         | Example                                       |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| **Income Certificate** | "income certificate", "income proof", "annual income", "gross income", "per annum"                               | Official income certificate from revenue dept |
| **Aadhaar**            | "aadhaar", "uid", "unique identification", "12-digit", "aadhaar number"                                          | Aadhaar card or document                      |
| **Caste Certificate**  | "caste certificate", "sc certificate", "st certificate", "obc certificate", "scheduled caste", "scheduled tribe" | SC/ST/OBC caste certificate                   |
| **Ration Card**        | "ration card", "ration", "fcs", "public distribution", "pds"                                                     | PDS ration card                               |
| **Land Record**        | "land record", "title deed", "property document", "land certificate", "7-12", "8-a"                              | Land ownership documents                      |

**Detection Confidence:**

- Confidence calculated as: `matched_keywords / total_keywords_for_type`
- Document type with highest confidence is selected
- If no keywords match, type is "unknown" with confidence 0.0

## Field Extraction

### Extracted Fields

The system attempts to extract the following fields using regex patterns:

| Field                  | Description              | Example                           |
| ---------------------- | ------------------------ | --------------------------------- |
| **name**               | Person's name            | "Rajesh Kumar Sharma"             |
| **income**             | Annual income in INR     | 150000                            |
| **certificate_number** | Document identifier      | "IC-2024-001"                     |
| **issue_date**         | Date of issuance         | "01/15/2024"                      |
| **issuing_authority**  | Organization that issued | "Revenue Department, Maharashtra" |

### Extraction Process

Each field is extracted using multiple regex patterns in sequence:

```python
# For income field, tries patterns like:
1. r"(?:annual income|gross income|income)[\\s:]*(?:Rs\\.?|INR)?[\\s]*([0-9,]+)"
2. r"(?:per annum|pa|yearly)[\\s]*(?:Rs\\.?|INR)?[\\s]*([0-9,]+)"
3. r"income[\\s]*(?:is|being|of)?[\\s]*(?:Rs\\.?|INR)?[\\s]*([0-9,]+)"
```

First matching pattern extracts the value. If no patterns match, field is set to `null`.

## Validation System

### Required Fields

Each document type has required fields that must be present:

| Document Type      | Required Fields                                   |
| ------------------ | ------------------------------------------------- |
| Income Certificate | income, certificate_number, issuing_authority     |
| Aadhaar            | certificate_number, name                          |
| Caste Certificate  | certificate_number, issuing_authority, issue_date |
| Ration Card        | name, certificate_number                          |
| Land Record        | certificate_number, issuing_authority             |
| Unknown            | name, certificate_number                          |

### Validation Rules

#### Income Validation

- Must be between 1,000 and 10,000,000 INR
- Returns error if outside range

#### Certificate Number Validation

- Minimum 5 characters
- For Aadhaar: Must match pattern `XXXX-XXXX-XXXX` (12 digits)
- For others: Alphanumeric with hyphens/slashes allowed

#### Date Validation

- Format: `DD/MM/YYYY` or `DD-MM-YYYY`
- Validates format only (not actual date value)

#### Profile Matching (Optional)

If `user_profile` is provided:

**Name Matching:**

- Compares first word of extracted name with first word of profile name
- Case-insensitive
- Returns mismatch issue if first names don't match

**Income Matching:**

- Allows ±20% variance from declared income
- Formula: `income * 0.8 <= extracted_income <= income * 1.2`
- Returns mismatch issue if outside range

## Confidence Scoring

Confidence score (0-100) is calculated using three components:

### Score Components

| Component                   | Points | Calculation                               |
| --------------------------- | ------ | ----------------------------------------- |
| **Presence Score**          | 50     | `(fields_present / required_fields) * 50` |
| **Format Validation Score** | 30     | `(valid_fields / checked_fields) * 30`    |
| **Text Quality Score**      | 20     | 20 if text > 100 chars, else 10           |

### Score Interpretation

| Score  | Interpretation                               |
| ------ | -------------------------------------------- |
| 80-100 | Excellent - document likely valid            |
| 60-79  | Good - document acceptable but some concerns |
| 40-59  | Fair - document needs review                 |
| 0-39   | Poor - significant concerns                  |

## Risk Assessment

Risk level determined by multiple factors:

| Risk Level | Condition                                      |
| ---------- | ---------------------------------------------- |
| **High**   | Suspicious indicators found OR confidence < 40 |
| **Medium** | Validation issues exist OR confidence < 60     |
| **Low**    | No issues and confidence >= 60                 |

### Suspicious Indicators

System detects and flags:

1. **Tampering Signs**: "whiteout", "correction", "modified" in text
2. **Photocopy Indicators**: "photocopy" present or "original" missing
3. **Aged Documents**: Issue date before 2015
4. **Fraud Keywords**: "fake", "dummy", "test", "sample" in text

## Response Status Field

The `status` field indicates verification result:

| Status         | Meaning                                                                              |
| -------------- | ------------------------------------------------------------------------------------ |
| **valid**      | High confidence (>=80) with no issues and valid profile match                        |
| **suspicious** | Suspicious indicators detected or moderate confidence (60-79) with validation issues |
| **mismatch**   | Profile doesn't match AND confidence > 50                                            |
| **invalid**    | Missing required fields or low confidence (<60)                                      |

## Usage Examples

### Example 1: Basic Income Certificate Verification

```bash
curl -X POST http://localhost:8000/document-verify \
  -F "file=@income_certificate.pdf"
```

**Response:**

```json
{
  "document_type": "income_certificate",
  "status": "valid",
  "confidence_score": 92,
  "extracted_fields": {
    "name": "Rajesh Kumar Sharma",
    "income": 200000,
    "certificate_number": "IC-MH-2024-001",
    "issue_date": "03/01/2024",
    "issuing_authority": "Revenue Department, Pune, Maharashtra"
  },
  "issues": [],
  "risk_level": "low",
  "validation_details": {
    "income_valid": true,
    "cert_num_valid": true,
    "date_valid": true,
    "profile_match": true
  }
}
```

### Example 2: Verification with Profile Matching

```bash
curl -X POST http://localhost:8000/document-verify \
  -F "file=@aadhaar.pdf" \
  -F "user_profile={\"name\": \"Rajesh Sharma\", \"income_inr\": 200000}"
```

**Response (with name mismatch):**

```json
{
  "document_type": "aadhaar",
  "status": "mismatch",
  "confidence_score": 75,
  "extracted_fields": {
    "name": "Raj Kumar",
    "income": null,
    "certificate_number": "3452 8765 4321",
    "issue_date": null,
    "issuing_authority": null
  },
  "issues": [
    "Name mismatch: document has 'Raj Kumar', user profile has 'Rajesh Sharma'"
  ],
  "risk_level": "medium",
  "validation_details": {
    "income_valid": true,
    "cert_num_valid": true,
    "date_valid": true,
    "profile_match": false
  }
}
```

### Example 3: Caste Certificate with Suspicious Indicators

```bash
curl -X POST http://localhost:8000/document-verify \
  -F "file=@old_cast_cert.pdf"
```

**Response (with dated certificate):**

```json
{
  "document_type": "caste_certificate",
  "status": "suspicious",
  "confidence_score": 58,
  "extracted_fields": {
    "name": "Suresh Rao",
    "income": null,
    "certificate_number": "CC-2014-5678",
    "issue_date": "12/20/2014",
    "issuing_authority": "District Collector, Karnataka"
  },
  "issues": ["Certificate is from 2014 (very old, may need renewal)"],
  "risk_level": "medium",
  "validation_details": {
    "income_valid": true,
    "cert_num_valid": true,
    "date_valid": true,
    "profile_match": true
  }
}
```

### Example 4: Scheme-Specific Verification

```bash
curl -X POST http://localhost:8000/verify-pdf \
  -F "req_json={\"scheme_id\": \"pm-kisan\", \"declared_documents\": [\"Aadhaar\", \"Land Records\", \"Bank Passbook\"]}" \
  -F "file=@documents.pdf"
```

**Response:**

```json
{
  "scheme_id": "pm-kisan",
  "scheme_name": "PM-KISAN (Prime Minister Kisan Samman Nidhi)",
  "required_documents": ["Aadhaar", "Land Records", "Bank Details"],
  "declared_documents": ["Aadhaar", "Land Records", "Bank Passbook"],
  "missing_declared": [],
  "pdf_found_keywords": {
    "Aadhaar": true,
    "Land Records": true,
    "Bank Details": true
  },
  "verdict": "Looks okay based on declared docs (and PDF keyword scan)."
}
```

## Integration Workflow

### Complete User Journey

```
1. User Uploads PDF + Optional Profile
   POST /document-verify

2. System Extracts Text from PDF
   extract_pdf_text(pdf_bytes)

3. Detects Document Type
   detect_document_type(text)
   → Returns (type, confidence)

4. Extracts Fields Using Regex
   extract_fields(text)
   → Returns ExtractedFields with all fields

5. Validates Fields
   - Check required fields present
   - Validate format (income range, cert# length, date format)
   - Match against user profile (if provided)
   - Detect suspicious indicators

6. Calculate Confidence Score
   presence_score + format_score + quality_score

7. Assess Risk Level
   Based on confidence, issues, suspicious indicators

8. Return VerificationResult
   {document_type, status, confidence_score, extracted_fields,
    issues, risk_level, validation_details}
```

## Error Handling

### Invalid PDF Upload

**Request:**

```bash
curl -X POST http://localhost:8000/document-verify \
  -F "file=@not_a_pdf.txt"
```

**Response:**

```json
{
  "detail": "Failed to read uploaded file"
}
```

**Status Code:** 400

### Invalid User Profile JSON

**Request:**

```bash
curl -X POST http://localhost:8000/document-verify \
  -F "file=@document.pdf" \
  -F "user_profile=invalid json"
```

**Response:**

```json
{
  "detail": "Invalid user_profile; must be valid JSON"
}
```

**Status Code:** 400

### PDF Text Extraction Failure

**Response (when PDF cannot be read):**

```json
{
  "document_type": "unknown",
  "status": "invalid",
  "confidence_score": 0,
  "extracted_fields": {},
  "issues": ["Failed to extract PDF text: PdfReadError"],
  "risk_level": "high",
  "validation_details": null
}
```

**Status Code:** 200 (returns verification result indicating failure)

## Performance Characteristics

| Operation                         | Time          | Notes                            |
| --------------------------------- | ------------- | -------------------------------- |
| Extract PDF text (max 200k chars) | 50-200ms      | Depends on PDF size/complexity   |
| Detect document type              | 1-5ms         | Keyword matching against 5 types |
| Extract fields (5 fields)         | 5-15ms        | Regex pattern matching           |
| Validate fields                   | 1-3ms         | Field format checks              |
| Profile matching                  | 1-2ms         | Simple string/number comparison  |
| **Total (typical)**               | **100-250ms** | End-to-end verification          |

## Data Flow Diagram

```
User PDF + Profile
        |
        v
extract_pdf_text()
   -> Raw text
        |
        v
detect_document_type()
   -> doc_type, confidence
        |
        v
extract_fields()
   -> name, income, cert_num, date, authority
        |
        v
get_required_fields(doc_type)
        |
        v
_validate_income_format()
_validate_certificate_number()
_validate_profile_match()
_check_suspicious_indicators()
        |
        v
_calculate_confidence()
   -> 0-100 score
        |
        v
_assess_risk_level()
   -> low/medium/high
        |
        v
return VerificationResult
```

## Future Enhancements

Potential improvements (not yet implemented):

- [ ] Machine learning-based document classification
- [ ] OCR for handwritten fields
- [ ] Digital signature verification
- [ ] Document authenticity checking
- [ ] Additional document types (PAN, Voter ID, etc.)
- [ ] Multi-language support
- [ ] Batch document verification
- [ ] Document expiration tracking
- [ ] Integration with NSDL/UIDAI APIs
- [ ] Advanced fraud detection patterns

## Support

For API documentation, see:

- `CHECK_ELIGIBILITY_EXAMPLES.md` - Eligibility endpoint usage
- `CHAT_API_DOCUMENTATION.md` - Chat endpoint usage
- `DATABASE_DOCUMENTATION.md` - Database operations
- `SYSTEM_OVERVIEW.md` - Complete system architecture

## Version

- **Version**: 0.1.0
- **Last Updated**: 2026-03-01
- **Status**: MVP (Minimum Viable Product)
