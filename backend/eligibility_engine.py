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
    official_link: str
    scoring_weights: dict[str, int]


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
                official_link=str(s.get("official_link", "")).strip(),
                scoring_weights=dict(s.get("scoring_weights", {}) or {}),
            )
        )
    _CACHE = schemes
    return schemes


def _norm(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    v = str(s).strip().lower()
    return v or None


def _evaluate_criteria(
    user: dict[str, Any], criteria: dict[str, Any], weights: dict[str, int]
) -> tuple[int, list[str], list[str]]:
    """
    Evaluate criteria against user profile and calculate score.

    Returns: (score, reasons, missing_criteria)
    """
    score = 0
    reasons: list[str] = []
    missing: list[str] = []

    # Extract and normalize user data
    age = user.get("age")
    income = user.get("income_inr")
    state = _norm(user.get("state"))
    category = _norm(user.get("category"))
    gender = _norm(user.get("gender"))
    occupation = _norm(user.get("occupation"))
    is_disabled = user.get("is_disabled")
    rural = user.get("rural")

    total_weight = sum(weights.values()) if weights else 100

    # Check min_age
    if "min_age" in criteria:
        weight = weights.get("min_age", 0)
        min_age = int(criteria["min_age"])
        if age is None:
            missing.append(f"min_age >= {min_age}")
        elif age >= min_age:
            score += weight
            reasons.append(f"Age {age} >= {min_age}")
        else:
            missing.append(f"min_age >= {min_age} (current: {age})")

    # Check max_age
    if "max_age" in criteria:
        weight = weights.get("max_age", 0)
        max_age = int(criteria["max_age"])
        if age is None:
            missing.append(f"max_age <= {max_age}")
        elif age <= max_age:
            score += weight
            reasons.append(f"Age {age} <= {max_age}")
        else:
            missing.append(f"max_age <= {max_age} (current: {age})")

    # Check max_income_inr
    if "max_income_inr" in criteria:
        weight = weights.get("max_income_inr", 0)
        max_income = int(criteria["max_income_inr"])
        if income is None:
            missing.append(f"income <= INR {max_income:,}")
        elif income <= max_income:
            score += weight
            reasons.append(f"Income INR {income:,} <= INR {max_income:,}")
        else:
            missing.append(f"income <= INR {max_income:,} (current: INR {income:,})")

    # Check min_income_inr
    if "min_income_inr" in criteria:
        weight = weights.get("min_income_inr", 0)
        min_income = int(criteria["min_income_inr"])
        if income is None:
            missing.append(f"income >= INR {min_income:,}")
        elif income >= min_income:
            score += weight
            reasons.append(f"Income INR {income:,} >= INR {min_income:,}")
        else:
            missing.append(f"income >= INR {min_income:,} (current: INR {income:,})")

    # Check state_any_of
    if "state_any_of" in criteria:
        weight = weights.get("state_any_of", 0)
        allowed = {_norm(x) for x in (criteria.get("state_any_of") or [])}
        allowed.discard(None)
        if state is None:
            missing.append(f"state in {allowed}")
        elif state in allowed:
            score += weight
            reasons.append(f"State {state} is eligible")
        else:
            missing.append(f"state not in allowed list (current: {state})")

    # Check category_any_of
    if "category_any_of" in criteria:
        weight = weights.get("category_any_of", 0)
        allowed = {_norm(x) for x in (criteria.get("category_any_of") or [])}
        allowed.discard(None)
        if category is None:
            missing.append(f"category in {allowed}")
        elif category in allowed:
            score += weight
            reasons.append(f"Category {category} is eligible")
        else:
            missing.append(f"category not in allowed list (current: {category})")

    # Check gender_any_of
    if "gender_any_of" in criteria:
        weight = weights.get("gender_any_of", 0)
        allowed = {_norm(x) for x in (criteria.get("gender_any_of") or [])}
        allowed.discard(None)
        if gender is None:
            missing.append(f"gender in {allowed}")
        elif gender in allowed:
            score += weight
            reasons.append(f"Gender {gender} is eligible")
        else:
            missing.append(f"gender not in allowed list (current: {gender})")

    # Check occupation_any_of
    if "occupation_any_of" in criteria:
        weight = weights.get("occupation_any_of", 0)
        allowed = {_norm(x) for x in (criteria.get("occupation_any_of") or [])}
        allowed.discard(None)
        if occupation is None:
            missing.append(f"occupation in {allowed}")
        elif occupation in allowed:
            score += weight
            reasons.append(f"Occupation {occupation} is eligible")
        else:
            missing.append(f"occupation not in allowed list (current: {occupation})")

    # Check is_disabled
    if "is_disabled" in criteria:
        weight = weights.get("is_disabled", 0)
        need = bool(criteria.get("is_disabled"))
        if is_disabled is None:
            missing.append(f"is_disabled = {need}")
        elif bool(is_disabled) == need:
            score += weight
            reasons.append(f"Disability status matches requirement ({need})")
        else:
            missing.append(f"is_disabled must be {need} (current: {is_disabled})")

    # Check rural
    if "rural_only" in criteria:
        weight = weights.get("rural_only", 0)
        if rural is None:
            missing.append("Rural area status required")
        elif rural:
            score += weight
            reasons.append("Rural area resident")
        else:
            missing.append("Must be in rural area")

    # Normalize score to 0-100 scale
    if total_weight > 0:
        normalized_score = int((score / total_weight) * 100)
    else:
        normalized_score = 0

    return normalized_score, reasons, missing


def evaluate_scheme(
    user: dict[str, Any], scheme: Scheme
) -> dict[str, Any]:
    """
    Evaluate a single scheme and return detailed eligibility info.
    """
    score, reasons, missing = _evaluate_criteria(user, scheme.criteria, scheme.scoring_weights)
    eligible = score >= 60

    return {
        "id": scheme.id,
        "scheme_name": scheme.name,
        "description": scheme.description,
        "benefits": scheme.benefits,
        "required_documents": scheme.documents_required,
        "score": score,
        "eligible": eligible,
        "reasons": reasons,
        "missing_criteria": missing,
        "official_link": scheme.official_link,
    }


def evaluate_eligibility(user: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate all schemes for the given user profile.

    Returns dict with:
    - best_match: highest scoring eligible scheme
    - eligible_schemes: all schemes with score >= 60
    - not_eligible_schemes: all schemes with score < 60
    """
    schemes = load_schemes()
    all_results = []

    for scheme in schemes:
        result = evaluate_scheme(user, scheme)
        all_results.append(result)

    # Separate eligible and not eligible
    eligible_schemes = [r for r in all_results if r["eligible"]]
    not_eligible_schemes = [r for r in all_results if not r["eligible"]]

    # Sort by score descending
    eligible_schemes.sort(key=lambda x: x["score"], reverse=True)
    not_eligible_schemes.sort(key=lambda x: x["score"], reverse=True)

    # Get best match
    best_match = eligible_schemes[0] if eligible_schemes else None

    return {
        "best_match": best_match,
        "eligible_schemes": eligible_schemes,
        "not_eligible_schemes": not_eligible_schemes,
    }


def get_scheme_by_id(scheme_id: str) -> Optional[Scheme]:
    sid = str(scheme_id).strip()
    for s in load_schemes():
        if s.id == sid:
            return s
    return None
