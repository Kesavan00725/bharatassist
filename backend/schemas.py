from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: Optional[str] = Field(default=None, description="Client-provided session id")
    user_profile: Optional[dict] = Field(default=None, description="User eligibility profile")
    eligibility_results: Optional[dict] = Field(default=None, description="Results from eligibility check")


class ChatResponse(BaseModel):
    session_id: str
    reply: str


class ChatResponseWithJSON(BaseModel):
    session_id: str
    reply: str
    scheme_suggestions: list[str] = []
    clarification_needed: list[str] = []


class EligibilityRequest(BaseModel):
    age: Optional[int] = Field(default=None, ge=0, le=120)
    income_inr: Optional[int] = Field(default=None, ge=0)
    state: Optional[str] = None
    category: Optional[str] = Field(
        default=None, description="e.g. sc/st/obc/ews/general"
    )
    gender: Optional[str] = Field(default=None, description="male/female/other")
    occupation: Optional[str] = None
    is_disabled: Optional[bool] = None
    rural: Optional[bool] = Field(default=None, description="Whether in rural area")


class SchemeOut(BaseModel):
    id: str
    scheme_name: str
    description: str
    benefits: list[str] = []
    required_documents: list[str] = []
    score: int
    eligible: bool
    reasons: list[str] = []
    missing_criteria: list[str] = []
    official_link: Optional[str] = None


class EligibilityResponse(BaseModel):
    best_match: Optional[SchemeOut] = None
    eligible_schemes: list[SchemeOut] = []
    not_eligible_schemes: list[SchemeOut] = []


class VerifyRequest(BaseModel):
    scheme_id: str
    declared_documents: list[str] = []


class VerifyResponse(BaseModel):
    scheme_id: str
    scheme_name: str
    required_documents: list[str]
    declared_documents: list[str]
    missing_declared: list[str]
    pdf_found_keywords: dict[str, bool] = {}
    verdict: str


class DocumentVerificationResponse(BaseModel):
    document_type: str
    status: str
    confidence_score: int
    extracted_fields: dict[str, Any]
    issues: list[str]
    risk_level: str
    validation_details: Optional[dict[str, Any]] = None


class HealthResponse(BaseModel):
    ok: bool
    details: dict[str, Any] = {}
