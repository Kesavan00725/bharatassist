from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: Optional[str] = Field(default=None, description="Client-provided session id")


class ChatResponse(BaseModel):
    session_id: str
    reply: str


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


class SchemeOut(BaseModel):
    id: str
    name: str
    description: str
    benefits: list[str] = []
    documents_required: list[str] = []
    matched_rules: list[str] = []


class EligibilityResponse(BaseModel):
    eligible: list[SchemeOut]
    not_eligible: list[SchemeOut]


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


class HealthResponse(BaseModel):
    ok: bool
    details: dict[str, Any] = {}
