from __future__ import annotations
from typing import Any, Dict, Optional


def score_risk(
    qr_text: str,
    meta: Optional[Dict[str, Any]] = None,
    ai_section: Optional[str] = None,
) -> int:
    """
    Very simple heuristic risk score for a QR payload.
    Returns an integer from 0 to 100.

    - Uses URL patterns (login, reset, etc.)
    - Uses metadata (qr_type, scheme, domain) if available.
    - Ignores ai_section for now, but kept in the signature for future use.
    """

    meta = meta or {}
    qr_type = meta.get("qr_type", "").lower()
    scheme = meta.get("scheme", "").lower()
    domain = str(meta.get("domain", "")).lower()
    path = str(meta.get("path", "")).lower()

    score = 10  # base

    # 1) نوع المحتوى
    if qr_type == "url":
        score += 10

    # 2) بروتوكول
    if scheme == "http":  # no TLS
        score += 25
    elif scheme == "https":
        score += 5

    # 3) كلمات مشبوهة في الـ URL
    risky_keywords = [
        "login",
        "signin",
        "reset",
        "verify",
        "update",
        "password",
        "2fa",
        "bank",
        "wallet",
    ]
    full = (domain + path + " " + qr_text).lower()
    for kw in risky_keywords:
        if kw in full:
            score += 15
            break

    # 4) IP-based links (بدل دومين)
    import re

    ip_pattern = re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b")
    if ip_pattern.search(full):
        score += 20

    # 5) لو الدومين غريب / طويل كثير
    if len(domain) > 25:
        score += 5

    # clamp 0–100
    if score < 0:
        score = 0
    if score > 100:
        score = 100

    return score
