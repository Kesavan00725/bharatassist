from __future__ import annotations

import json

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from chat_service import chat_reply, get_or_create_session_id
from database import init_db
from document_verifier import compare_declared_to_required, extract_pdf_text, keyword_presence
from eligibility_engine import evaluate_eligibility, get_scheme_by_id, load_schemes
from schemas import (
    ChatRequest,
    ChatResponse,
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
    reply = chat_reply(session_id=session_id, user_message=req.message)
    return ChatResponse(session_id=session_id, reply=reply)


@app.post("/eligibility", response_model=EligibilityResponse)
def eligibility(req: EligibilityRequest) -> EligibilityResponse:
    eligible, not_eligible = evaluate_eligibility(req.model_dump())
    return EligibilityResponse(eligible=eligible, not_eligible=not_eligible)


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

