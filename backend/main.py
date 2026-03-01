from __future__ import annotations

import json

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from chat_service import chat_reply, chat_reply_with_json, get_or_create_session_id
from database import init_db
from document_verifier import (
    compare_declared_to_required,
    extract_pdf_text,
    keyword_presence,
    verify_pdf_document,
)
from eligibility_engine import evaluate_eligibility, get_scheme_by_id, load_schemes
from schemas import (
    ChatRequest,
    ChatResponse,
    ChatResponseWithJSON,
    DocumentVerificationResponse,
    EligibilityRequest,
    EligibilityResponse,
    HealthResponse,
    VerifyRequest,
    VerifyResponse,
)


app = FastAPI(title="BharatAssist MVP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    load_schemes()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(ok=True, details={"service": "bharatassist-backend"})


@app.get("/schemes")
def schemes():
    return {"schemes": [s.__dict__ for s in load_schemes()]}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    session_id = get_or_create_session_id(req.session_id)
    reply = chat_reply(
        session_id=session_id,
        user_message=req.message,
        user_profile=req.user_profile,
        eligibility_results=req.eligibility_results,
    )
    return ChatResponse(session_id=session_id, reply=reply)


@app.post("/chat-with-json", response_model=ChatResponseWithJSON)
def chat_with_json(req: ChatRequest) -> ChatResponseWithJSON:
    """
    Chat endpoint that returns structured JSON with scheme suggestions and clarification needs.

    Request includes:
    - message: user's question
    - session_id: optional chat session id
    - user_profile: optional user data (age, income, state, etc.)
    - eligibility_results: optional results from /check-eligibility endpoint

    Response includes:
    - reply: assistant message text
    - scheme_suggestions: list of relevant scheme IDs
    - clarification_needed: list of missing profile fields
    """
    session_id = get_or_create_session_id(req.session_id)
    result = chat_reply_with_json(
        session_id=session_id,
        user_message=req.message,
        user_profile=req.user_profile,
        eligibility_results=req.eligibility_results,
    )
    return ChatResponseWithJSON(
        session_id=session_id,
        reply=result["reply"],
        scheme_suggestions=result.get("scheme_suggestions", []),
        clarification_needed=result.get("clarification_needed", []),
    )


@app.post("/eligibility", response_model=EligibilityResponse)
def eligibility(req: EligibilityRequest) -> EligibilityResponse:
    result = evaluate_eligibility(req.model_dump())
    return EligibilityResponse(
        best_match=result["best_match"],
        eligible_schemes=result["eligible_schemes"],
        not_eligible_schemes=result["not_eligible_schemes"],
    )


@app.post("/check-eligibility", response_model=EligibilityResponse)
def check_eligibility(req: EligibilityRequest) -> EligibilityResponse:
    """
    Check eligibility for government schemes.

    Input fields:
    - age: integer (0-120)
    - income_inr: annual income in INR
    - state: state name
    - category: sc/st/obc/ews/general
    - occupation: e.g., farmer, student, retired
    - is_disabled: boolean
    - rural: boolean (whether in rural area)

    Returns:
    - best_match: highest scoring eligible scheme
    - eligible_schemes: all schemes with score >= 60
    - not_eligible_schemes: all schemes with score < 60
    """
    result = evaluate_eligibility(req.model_dump())
    return EligibilityResponse(
        best_match=result["best_match"],
        eligible_schemes=result["eligible_schemes"],
        not_eligible_schemes=result["not_eligible_schemes"],
    )


@app.post("/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest) -> VerifyResponse:
    scheme = get_scheme_by_id(req.scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Unknown scheme_id")

    required = scheme.documents_required or []
    missing_declared = compare_declared_to_required(req.declared_documents, required)

    verdict = (
        "Missing required documents (declared list incomplete)."
        if missing_declared
        else "Looks okay based on declared docs."
    )

    return VerifyResponse(
        scheme_id=scheme.id,
        scheme_name=scheme.name,
        required_documents=required,
        declared_documents=req.declared_documents,
        missing_declared=missing_declared,
        pdf_found_keywords={},
        verdict=verdict,
    )


@app.post("/verify-pdf", response_model=VerifyResponse)
async def verify_pdf(
    req_json: str = Form(..., description="JSON string matching VerifyRequest"),
    file: UploadFile = File(...),
) -> VerifyResponse:
    try:
        req = VerifyRequest(**json.loads(req_json))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid req_json; must be VerifyRequest JSON")

    scheme = get_scheme_by_id(req.scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Unknown scheme_id")

    required = scheme.documents_required or []
    missing_declared = compare_declared_to_required(req.declared_documents, required)

    pdf_bytes = await file.read()
    text = extract_pdf_text(pdf_bytes)
    pdf_found = keyword_presence(text, required)

    if missing_declared and (not pdf_found or not any(pdf_found.values())):
        verdict = "Missing required documents (declared and/or not detected in PDF)."
    elif missing_declared:
        verdict = "Some required documents not declared; PDF may contain partial evidence."
    else:
        verdict = "Looks okay based on declared docs (and PDF keyword scan)."

    return VerifyResponse(
        scheme_id=scheme.id,
        scheme_name=scheme.name,
        required_documents=required,
        declared_documents=req.declared_documents,
        missing_declared=missing_declared,
        pdf_found_keywords=pdf_found,
        verdict=verdict,
    )


@app.post("/document-verify", response_model=DocumentVerificationResponse)
async def document_verify(
    file: UploadFile = File(..., description="PDF file to verify"),
    user_profile: Optional[str] = Form(None, description="Optional JSON string with user profile data"),
) -> DocumentVerificationResponse:
    """
    Comprehensive PDF document verification with extraction and validation.

    This endpoint performs detailed verification including:
    - Document type detection (Income Certificate, Aadhaar, Caste Certificate, etc.)
    - Field extraction (name, income, certificate number, issue date, authority)
    - Format validation
    - Profile matching (if user_profile provided)
    - Suspicious indicator detection
    - Confidence scoring (0-100)
    - Risk assessment (low/medium/high)

    Parameters:
    - file: PDF file upload
    - user_profile: Optional JSON with {"name", "income_inr", ...} for validation

    Returns:
    - document_type: Detected type or "unknown"
    - status: "valid" | "suspicious" | "mismatch" | "invalid"
    - confidence_score: 0-100 score based on extraction quality
    - extracted_fields: {"name", "income", "certificate_number", "issue_date", "issuing_authority"}
    - issues: List of validation issues found
    - risk_level: "low" | "medium" | "high"
    - validation_details: Detailed validation results
    """
    try:
        user_profile_dict = None
        if user_profile:
            user_profile_dict = json.loads(user_profile)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_profile; must be valid JSON")

    try:
        pdf_bytes = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")

    result = verify_pdf_document(pdf_bytes, user_profile_dict)

    return DocumentVerificationResponse(
        document_type=result.document_type,
        status=result.status,
        confidence_score=result.confidence_score,
        extracted_fields=result.extracted_fields,
        issues=result.issues,
        risk_level=result.risk_level,
        validation_details=result.validation_details,
    )

