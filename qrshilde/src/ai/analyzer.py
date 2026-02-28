from __future__ import annotations

import datetime
import os
import re
import socket
import uuid
from urllib.parse import urlparse

from qrshilde.src.tools.malicious_pattern_detector import scan_for_patterns
from qrshilde.src.tools.wifi_auto_connect_detector import detect_wifi_threats
from qrshilde.src.tools.payload_type import detect_payload_type
from qrshilde.src.ml.url_model import predict_url, model_exists
from qrshilde.src.ai.report_generator import build_markdown_report

DEFAULT_THRESHOLD = float(os.getenv("URL_MAL_THRESHOLD", "0.60"))

ALLOWLIST_DOMAINS = {"google.com", "github.com", "microsoft.com", "paypal.com"}

RESERVED_DOMAINS = {"example.com", "example.net", "example.org", "localhost", "127.0.0.1"}

SHORTENERS = {
    "bit.ly", "t.co", "tinyurl.com", "goo.gl", "is.gd", "buff.ly", "cutt.ly",
    "ow.ly", "rebrand.ly", "lnk.bio", "shorturl.at"
}

BRANDS = ["paypal", "google", "microsoft", "apple", "netflix", "binance"]

LURE_WORDS = [
    "login", "verify", "update", "secure", "account", "password", "otp", "bank",
    "confirm", "billing", "invoice", "pay", "wallet", "support"
]


def _get_domain(url: str) -> str | None:
    try:
        u = (url or "").strip()
        if "://" not in u:
            u = "http://" + u
        parsed = urlparse(u)
        host = (parsed.hostname or "").lower().strip(".")
        if not host:
            return None
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return None


def _domain_in_set(domain: str, s: set[str]) -> bool:
    d = (domain or "").lower().strip(".")
    for base in s:
        b = (base or "").lower().strip(".")
        if d == b or d.endswith("." + b):
            return True
    return False


def _dns_resolves(domain: str) -> bool:
    try:
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False


def _count_dashes(domain: str) -> int:
    return domain.count("-") if domain else 0


def _url_is_http(url: str) -> bool:
    u = (url or "").strip().lower()
    return u.startswith("http://")


def _lure_hits(text: str) -> list[str]:
    t = (text or "").lower()
    return [w for w in LURE_WORDS if w in t]


def _extract_url_from_vcard(payload: str) -> str | None:
    m = re.search(r"(?im)^\s*URL\s*:\s*(.+?)\s*$", payload or "")
    if m:
        return m.group(1).strip()
    m2 = re.search(r"(https?://[^\s]+)", payload or "", flags=re.IGNORECASE)
    return m2.group(1).strip() if m2 else None


def _sms_threats(payload: str) -> list[str]:
    p = (payload or "").strip()
    up = p.upper()
    threats = []
    if up.startswith(("SMSTO:", "SMS:")):
        threats.append("SMS QR: May trigger composing/sending an SMS (social engineering risk).")
        if any(k in p.lower() for k in ["bank", "otp", "verify", "urgent", "money", "transfer", "payment"]):
            threats.append("SMS Heuristic: smishing keywords detected (otp/bank/urgent/verify/...)")
    return threats


def _tel_threats(payload: str) -> list[str]:
    p = (payload or "").strip().lower()
    threats = []
    if p.startswith("tel:"):
        threats.append("TEL QR: Can initiate a phone call—common for scam call redirection.")
    return threats


def _email_threats(payload: str) -> list[str]:
    p = (payload or "").strip()
    up = p.upper()
    threats = []
    if p.lower().startswith("mailto:") or up.startswith("MATMSG:"):
        threats.append("EMAIL QR: May prefill an email (phishing/social engineering risk).")
        if any(k in p.lower() for k in ["password", "otp", "verify", "urgent", "invoice", "payment", "bank"]):
            threats.append("Email Heuristic: phishing keywords detected (otp/bank/urgent/verify/...)")
    return threats


def _vcard_threats(payload: str) -> list[str]:
    up = (payload or "").upper()
    threats = []
    if up.startswith("BEGIN:VCARD") or "VCARD" in up:
        threats.append("VCARD QR: Can import contact data—may hide malicious URLs in fields.")
        if "URL:" in up or "HTTP" in up:
            threats.append("VCARD contains URL fields—verify before opening embedded links.")
    return threats


def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def _verdict_from_score(score: int) -> str:
    if score >= 80:
        return "HIGH"
    if score >= 45:
        return "MEDIUM"
    return "LOW"


async def analyze_qr_payload(payload: str, report_id: str):
    payload = (payload or "").strip()
    findings: list[str] = []
    benign: list[str] = []
    risk_score = 0

    if not report_id or not str(report_id).strip():
        report_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]

    # 0) Detect type
    ptype = detect_payload_type(payload)
    findings.append(f"Payload type: {ptype}")

    # 1) General Pattern Scan
    pattern_issues = scan_for_patterns(payload)
    if pattern_issues:
        findings.extend(pattern_issues)
        risk_score += 40
    else:
        benign.append("No obvious injection patterns found (basic regex scan).")

    # 2) Payload-specific rules
    payload_for_url = None
    ptype_for_url = None

    if ptype == "wifi":
        wifi_issues = detect_wifi_threats(payload)
        if wifi_issues:
            findings.extend(wifi_issues)
            risk_score += 40
        else:
            benign.append("Wi-Fi payload parsed with no strong threat flags.")

    elif ptype == "sms":
        sms_issues = _sms_threats(payload)
        if sms_issues:
            findings.extend(sms_issues)
            risk_score += 45

    elif ptype == "tel":
        tel_issues = _tel_threats(payload)
        if tel_issues:
            findings.extend(tel_issues)
            risk_score += 20

    elif ptype == "email":
        email_issues = _email_threats(payload)
        if email_issues:
            findings.extend(email_issues)
            risk_score += 25

    elif ptype == "vcard":
        vcard_issues = _vcard_threats(payload)
        if vcard_issues:
            findings.extend(vcard_issues)
            risk_score += 20

        embedded_url = _extract_url_from_vcard(payload)
        if embedded_url:
            findings.append("VCARD: embedded URL extracted for analysis.")
            payload_for_url = embedded_url
            ptype_for_url = "url"

    elif ptype == "deeplink":
        findings.append("Deep link QR: May open apps directly (higher risk if unexpected).")
        risk_score += 20

    # 3) URL heuristics (for URL payload OR embedded URL in vcard)
    url_target = payload if ptype == "url" else payload_for_url

    domain = None
    is_allowlisted = False
    is_reserved = False
    is_shortener = False
    dns_ok = True

    if url_target and (ptype == "url" or ptype_for_url == "url"):
        domain = _get_domain(url_target)

        if domain:
            if _domain_in_set(domain, ALLOWLIST_DOMAINS):
                is_allowlisted = True
                benign.append(f"Allowlist match: {domain}")

            if _domain_in_set(domain, RESERVED_DOMAINS):
                is_reserved = True
                benign.append(f"Reserved/documentation domain: {domain} (lower concern)")

            if _domain_in_set(domain, SHORTENERS):
                is_shortener = True
                findings.append(f"URL Heuristic: shortener detected ({domain})")
                risk_score += 25

            for brand in BRANDS:
                if brand in domain and not domain.endswith(f"{brand}.com"):
                    findings.append(f"URL Heuristic: possible brand impersonation in domain ({brand})")
                    risk_score += 35
                    break

            if _count_dashes(domain) >= 2:
                findings.append("URL Heuristic: excessive dashes in domain")
                risk_score += 10

            if (not is_allowlisted) and (not is_reserved) and (not _dns_resolves(domain)):
                dns_ok = False
                findings.append("URL Heuristic: domain does not resolve (NXDOMAIN/DNS failure)")
                risk_score += 25

        if _url_is_http(url_target):
            findings.append("URL Heuristic: HTTP without TLS")
            risk_score += 10
        else:
            benign.append("HTTPS detected (or non-http scheme).")

        hits = _lure_hits(url_target)
        if hits and not is_allowlisted and not is_reserved:
            findings.append(f"URL Heuristic: lure keywords detected: {', '.join(hits[:8])}")
            risk_score += 15
        elif hits and (is_allowlisted or is_reserved):
            benign.append("Lure-like words exist but domain is allowlisted/reserved (reduced concern).")

    # 4) ML model (URL only)
    ml_result = None
    if url_target and (ptype == "url" or ptype_for_url == "url") and model_exists():
        try:
            ml_result = predict_url(url_target)
            p = float(ml_result.get("phishing_probability", 0.0))
            thr = float(ml_result.get("threshold", DEFAULT_THRESHOLD))

            if p >= thr:
                findings.append(f"ML: suspicious probability={p:.2f} (>= {thr:.2f})")
                risk_score += 35
            else:
                benign.append(f"ML: probability={p:.2f} (< {thr:.2f})")
                risk_score -= 5

            if is_shortener and p >= thr:
                risk_score += 10

        except Exception as e:
            findings.append(f"ML: model error: {e}")
    else:
        if url_target and (ptype == "url" or ptype_for_url == "url"):
            benign.append("ML model not found (url_model.pkl missing) — rules-only mode.")

    # 5) Final normalize
    risk_score = _clamp(risk_score, 0, 100)

    meta = {
        "report_id": report_id,
        "payload_type": ptype,
        "domain": domain,
        "dns_resolves": dns_ok if domain else None,
        "allowlisted": is_allowlisted,
        "reserved_domain": is_reserved,
        "shortener": is_shortener,
        "verdict_band": _verdict_from_score(risk_score),
    }

    analysis = {
        "payload": payload,
        "meta": meta,
        "risk_score": risk_score,
        "findings": findings,
        "benign_signals": benign,
        "ml": ml_result,
    }

    analysis["report_md"] = build_markdown_report({
        "payload": payload,
        "meta": meta,
        "risk_score": risk_score,
        "ai_report": "",  # no AI
    })

    return analysis