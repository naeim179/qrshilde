# qrshilde/src/analysis/classifier.py

from __future__ import annotations
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, List


def extract_basic_meta(qr_text: str) -> Dict[str, Any]:
    """
    Try to detect the basic type of QR payload and extract metadata.
    Right now we focus on URL payloads.
    """
    qr_text = qr_text.strip()
    meta: Dict[str, Any] = {
        "qr_type": "text",
        "scheme": None,
        "domain": None,
        "path": None,
        "query": None,
        "is_url": False,
    }

    # بسيط: لو فيه http أو https نعتبره URL
    if qr_text.lower().startswith(("http://", "https://")):
        parsed = urlparse(qr_text)
        meta["qr_type"] = "URL"
        meta["is_url"] = True
        meta["scheme"] = parsed.scheme
        meta["domain"] = parsed.netloc.lower()
        meta["path"] = parsed.path or "/"
        meta["query"] = parse_qs(parsed.query) if parsed.query else {}
        return meta

    # TODO: ممكن نضيف أنواع ثانية: WIFI:, SMSTO:, VCARD, إلخ
    return meta


def detect_attacks(qr_text: str, meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Rule-based detection for potential attacks based on the payload + metadata.
    This is pure logic (no AI).
    Returns a list of attack objects like:
    {
      "id": "login_page_url",
      "title": "Login-like URL",
      "severity": "medium",
      "reason": "..."
    }
    """
    attacks: List[Dict[str, Any]] = []
    qr_text = qr_text.strip()

    # لو مش URL ما نحلل كثير الآن
    if not meta.get("is_url"):
        return attacks

    domain = (meta.get("domain") or "").lower()
    path = (meta.get("path") or "").lower()
    query = meta.get("query") or {}

    # 1) Login-like URL (login/signin/auth في الـ path)
    login_keywords = ["login", "signin", "sign-in", "auth", "authenticate"]
    if any(k in path for k in login_keywords):
        attacks.append({
            "id": "login_page_url",
            "title": "Login-like URL",
            "severity": "medium",
            "reason": f"Path '{path}' contains login-related keyword; might be a phishing login page.",
        })

    # 2) Suspicious-looking domain (كثير hyphens أو طول غريب)
    if domain:
        hyphen_count = domain.count("-")
        if hyphen_count >= 3 or len(domain) > 40:
            attacks.append({
                "id": "suspicious_domain_pattern",
                "title": "Suspicious-looking domain",
                "severity": "medium",
                "reason": f"Domain '{domain}' looks unusual (many hyphens or long length).",
            })

    # 3) QRLjacking candidate (دومينات login/session شائعة)
    # ملاحظة: هذا heuristic بسيط، مش فحص reputation حقيقي
    known_login_domains = [
        "web.whatsapp.com",
        "accounts.google.com",
        "login.microsoftonline.com",
        "discord.com",
        "discordapp.com",
        "telegram.org",
        "t.me",
    ]

    if domain in known_login_domains:
        token_like_params = {"token", "session", "sess", "auth", "code"}
        q_keys = set(k.lower() for k in query.keys())
        if q_keys & token_like_params:
            attacks.append({
                "id": "qrljacking_candidate",
                "title": "QRLjacking candidate",
                "severity": "high",
                "reason": (
                    f"URL points to a well-known login domain ({domain}) "
                    f"and contains token/session-like parameters; could be used for QRLjacking."
                ),
            })

    return attacks
