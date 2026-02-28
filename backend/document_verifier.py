from __future__ import annotations

import re
from typing import Optional

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
