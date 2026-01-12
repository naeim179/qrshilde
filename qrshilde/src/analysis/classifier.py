# qrshilde/src/analysis/classifier.py

from __future__ import annotations
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, List
import re  # نحتاج مكتبة re عشان البحث عن التوكنات

def extract_basic_meta(qr_text: str) -> Dict[str, Any]:
    """
    Try to detect the basic type of QR payload and extract metadata.
    Supported: URL, WIFI, SMSTO, TEL, MAILTO, Text.
    """
    qr_text = qr_text.strip()
    meta: Dict[str, Any] = {
        "qr_type": "text",
        "scheme": None,
        "domain": None,
        "path": None,
        "query": None,
        "is_url": False,
        "wifi_info": None, # إضافة جديدة لمعلومات الواي فاي
    }

    # 1. فحص الروابط (URL)
    if qr_text.lower().startswith(("http://", "https://")):
        parsed = urlparse(qr_text)
        meta["qr_type"] = "URL"
        meta["is_url"] = True
        meta["scheme"] = parsed.scheme
        meta["domain"] = parsed.netloc.lower()
        meta["path"] = parsed.path or "/"
        meta["query"] = parse_qs(parsed.query) if parsed.query else {}
        return meta

    # 2. فحص الواي فاي (WIFI)
    if qr_text.upper().startswith("WIFI:"):
        meta["qr_type"] = "WIFI"
        meta["scheme"] = "wifi"
        # استخراج اسم الشبكة بشكل بسيط
        ssid_match = re.search(r'S:([^;]+)', qr_text)
        meta["wifi_info"] = {"ssid": ssid_match.group(1)} if ssid_match else {}
        return meta

    # 3. فحص الرسائل والاتصال (SMS, TEL, MAILTO)
    if qr_text.upper().startswith("SMSTO:"):
        meta["qr_type"] = "SMS"
        meta["scheme"] = "sms"
        return meta
    
    if qr_text.upper().startswith("TEL:"):
        meta["qr_type"] = "TEL"
        meta["scheme"] = "tel"
        return meta

    return meta


def detect_attacks(qr_text: str, meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Rule-based detection for potential attacks based on the payload + metadata.
    Includes: Secrets detection, Injection patterns, and URL heuristics.
    """
    attacks: List[Dict[str, Any]] = []
    qr_text = qr_text.strip()

    # --- الجزء الأول: كشف الأسرار والتوكنات (يعمل على أي نص) ---
    secrets_patterns = {
        "Possible JWT Token": r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
        "Google API Key": r'AIza[0-9A-Za-z-_]{35}',
        "AWS Access Key": r'AKIA[0-9A-Z]{16}',
        "Private Key": r'-----BEGIN (?:RSA|DSA|EC|PGP) PRIVATE KEY-----',
    }

    for name, pattern in secrets_patterns.items():
        if re.search(pattern, qr_text):
            attacks.append({
                "id": "sensitive_data_exposure",
                "title": f"Sensitive Data Found: {name}",
                "severity": "critical",
                "reason": f"The QR content contains a pattern matching a {name}.",
            })

    # --- الجزء الثاني: كشف هجمات الحقن (Injection) ---
    injection_patterns = {
        "SQL Injection": r'(?i)(\' OR 1=1|UNION SELECT|DROP TABLE|--)',
        "XSS Payload": r'(?i)(<script>|javascript:|onerror=)',
        "Command Injection": r'(?i)(;|\||&&|\$\(|\`)(cat|nc|wget|curl|rm|whoami)',
        "Path Traversal": r'(\.\./\.\./|/etc/passwd|c:\\windows)',
    }

    for name, pattern in injection_patterns.items():
        if re.search(pattern, qr_text):
            attacks.append({
                "id": "injection_attack",
                "title": f"Injection Attempt: {name}",
                "severity": "high",
                "reason": f"Suspicious syntax detected matching {name}.",
            })

    # --- الجزء الثالث: تحليل الروابط (نفس كودك السابق مع تحسينات طفيفة) ---
    if meta.get("is_url"):
        domain = (meta.get("domain") or "").lower()
        path = (meta.get("path") or "").lower()
        query = meta.get("query") or {}

        # 1) Login-like URL
        login_keywords = ["login", "signin", "sign-in", "auth", "authenticate"]
        if any(k in path for k in login_keywords):
            attacks.append({
                "id": "login_page_url",
                "title": "Login-like URL",
                "severity": "medium",
                "reason": f"Path '{path}' contains login-related keyword.",
            })

        # 2) Suspicious domain
        if domain:
            hyphen_count = domain.count("-")
            if hyphen_count >= 3 or len(domain) > 40:
                attacks.append({
                    "id": "suspicious_domain_pattern",
                    "title": "Suspicious-looking domain",
                    "severity": "medium",
                    "reason": f"Domain '{domain}' looks unusual.",
                })

        # 3) QRLjacking candidate
        known_login_domains = [
            "web.whatsapp.com", "accounts.google.com", "login.microsoftonline.com",
            "discord.com", "discordapp.com", "telegram.org", "t.me",
        ]

        if domain in known_login_domains:
            token_like_params = {"token", "session", "sess", "auth", "code"}
            q_keys = set(k.lower() for k in query.keys())
            if q_keys & token_like_params:
                attacks.append({
                    "id": "qrljacking_candidate",
                    "title": "QRLjacking Candidate",
                    "severity": "high",
                    "reason": f"URL points to {domain} with session parameters.",
                })

    return attacks