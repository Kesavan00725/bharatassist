from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


SCHEMES_PATH = Path(__file__).resolve().parent / "schemes.json"


@dataclass
class Scheme:
    id: str
    name: str
    description: str
    benefits: list[str]
    documents_required: list[str]
    criteria: dict[str, Any]


_CACHE: Optional[list[Scheme]] = None


def load_schemes() -> list[Scheme]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    data = json.loads(SCHEMES_PATH.read_text(encoding="utf-8"))
    schemes: list[Scheme] = []
    for s in data.get("schemes", []):
        schemes.append(
            Scheme(
                id=str(s.get("id", "")).strip(),
                name=str(s.get("name", "")).strip(),
                description=str(s.get("description", "")).strip(),
                benefits=list(s.get("benefits", []) or []),
                documents_required=list(s.get("documents_required", []) or []),
                criteria=dict(s.get("criteria", {}) or {}),
            )
        )
    _CACHE = schemes
    return schemes


def _norm(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    v = str(s).strip().lower()
    return v or None


def _match_criteria(user: dict[str, Any], criteria: dict[str, Any]) -> tuple[bool, list[str]]:
    matched: list[str] = []

    def ok(rule: str) -> None:
        matched.append(rule)

    age = user.get("age")
    income = user.get("income_inr")
    state = _norm(user.get("state"))
    category = _norm(user.get("category"))
    gender = _norm(user.get("gender"))
    occupation = _norm(user.get("occupation"))
    is_disabled = user.get("is_disabled")

    if "min_age" in criteria:
        if age is None or age < int(criteria["min_age"]):
            return False, matched
        ok(f"age >= {criteria['min_age']}")

    if "max_age" in criteria:
        if age is None or age > int(criteria["max_age"]):
            return False, matched
        ok(f"age <= {criteria['max_age']}")

    if "max_income_inr" in criteria:
        if income is None or income > int(criteria["max_income_inr"]):
            return False, matched
        ok(f"income <= {criteria['max_income_inr']}")

    if "state_any_of" in criteria:
        allowed = {_norm(x) for x in (criteria.get("state_any_of") or [])}
        allowed.discard(None)
        if state is None or state not in allowed:
            return False, matched
        ok("state allowed")

    if "category_any_of" in criteria:
        allowed = {_norm(x) for x in (criteria.get("category_any_of") or [])}
        allowed.discard(None)
        if category is None or category not in allowed:
            return False, matched
        ok("category allowed")

    if "gender_any_of" in criteria:
        allowed = {_norm(x) for x in (criteria.get("gender_any_of") or [])}
        allowed.discard(None)
        if gender is None or gender not in allowed:
            return False, matched
        ok("gender allowed")

    if "occupation_any_of" in criteria:
        allowed = {_norm(x) for x in (criteria.get("occupation_any_of") or [])}
        allowed.discard(None)
        if occupation is None or occupation not in allowed:
            return False, matched
        ok("occupation allowed")

    if "is_disabled" in criteria:
        need = bool(criteria.get("is_disabled"))
        if is_disabled is None or bool(is_disabled) != need:
            return False, matched
        ok(f"is_disabled == {need}")

    return True, matched


def evaluate_eligibility(user: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    eligible: list[dict[str, Any]] = []
    not_eligible: list[dict[str, Any]] = []
    for s in load_schemes():
        ok, matched = _match_criteria(user, s.criteria)
        base = {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "benefits": s.benefits,
            "documents_required": s.documents_required,
            "matched_rules": matched,
        }
        (eligible if ok else not_eligible).append(base)
    return eligible, not_eligible


def get_scheme_by_id(scheme_id: str) -> Optional[Scheme]:
    sid = str(scheme_id).strip()
    for s in load_schemes():
        if s.id == sid:
            return s
    return None
