import datetime
import ipaddress
import os
import re
import socket
import uuid
from urllib.parse import unquote, urlparse

from qrshilde.analysis.report_generator import build_markdown_report
from qrshilde.detectors.malicious_pattern_detector import scan_for_patterns_detailed
from qrshilde.detectors.payload_type import detect_payload_type
from qrshilde.detectors.wifi_auto_connect_detector import detect_wifi_threats
from qrshilde.ml.url_model import model_exists, predict_url

# -----------------------------
# Config
# -----------------------------
ALLOWLIST_DOMAINS = {
    "google.com",
    "github.com",
    "microsoft.com",
    "paypal.com",
}

RESERVED_DOMAINS = {
    "example.com",
    "example.net",
    "example.org",
    "localhost",
    "127.0.0.1",
}

SHORTENERS = {
    "bit.ly",
    "t.co",
    "tinyurl.com",
    "goo.gl",
    "is.gd",
    "buff.ly",
    "cutt.ly",
    "ow.ly",
    "rebrand.ly",
    "lnk.bio",
    "shorturl.at",
}

LURE_WORDS = {
    "login",
    "verify",
    "update",
    "secure",
    "account",
    "password",
    "otp",
    "bank",
    "confirm",
    "billing",
    "invoice",
    "pay",
    "wallet",
    "support",
    "gift",
    "free",
}

DANGEROUS_URL_SCHEMES = {"javascript", "data", "vbscript", "file", "intent"}
DANGEROUS_FILE_EXTENSIONS = {"exe", "msi", "apk", "bat", "cmd", "ps1", "jar", "js", "vbs"}

ENABLE_DNS_CHECK = os.getenv("QRSHILDE_ENABLE_DNS_CHECK", "0").strip() == "1"
DNS_TIMEOUT_SECONDS = float(os.getenv("QRSHILDE_DNS_TIMEOUT", "1.5"))

SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")


# -----------------------------
# Helpers
# -----------------------------
def _clamp(value: float | int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, int(round(value))))


def _append_unique(target: list[str], value: str) -> None:
    if value not in target:
        target.append(value)


def _new_report_id() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]


def _safe_parse_url(value: str):
    candidate = (value or "").strip()
    if not candidate:
        return urlparse("")

    if SCHEME_RE.match(candidate):
        return urlparse(candidate)

    return urlparse("https://" + candidate)


def _normalize_domain(hostname: str | None) -> str | None:
    if not hostname:
        return None
    host = hostname.lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    return host or None


def _domain_in_set(domain: str | None, values: set[str]) -> bool:
    d = (domain or "").lower().strip(".")
    if not d:
        return False

    for base in values:
        b = (base or "").lower().strip(".")
        if d == b or d.endswith("." + b):
            return True
    return False


def _dns_resolves(domain: str | None) -> bool | None:
    if not domain or not ENABLE_DNS_CHECK:
        return None

    try:
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(DNS_TIMEOUT_SECONDS)
        try:
            socket.gethostbyname(domain)
            return True
        finally:
            socket.setdefaulttimeout(old_timeout)
    except Exception:
        return False


def _host_is_ip(hostname: str | None) -> bool:
    if not hostname:
        return False
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def _extract_url_from_vcard(payload: str) -> str | None:
    if not payload:
        return None

    match = re.search(r"(?im)^\s*(?:item\d+\.)?URL\s*:\s*(.+?)\s*$", payload)
    if match:
        return match.group(1).strip()

    return _extract_first_url_anywhere(payload)


def _extract_url_from_mecard(payload: str) -> str | None:
    if not payload:
        return None

    match = re.search(r"(?i)(?:^|;)URL:((?:\\.|[^;])*)", payload)
    if match:
        return match.group(1).strip().replace(r"\;", ";").replace(r"\:", ":")

    return _extract_first_url_anywhere(payload)


def _extract_first_url_anywhere(payload: str) -> str | None:
    if not payload:
        return None

    match = re.search(r'((?:https?://|www\.)[^\s<>"\']+)', payload, flags=re.IGNORECASE)
    if match:
        return match.group(1).rstrip("),.;]}>")

    return None


def _extract_lure_hits(text: str) -> list[str]:
    tokens = set(re.findall(r"[a-z0-9]+", (text or "").lower()))
    hits = sorted(w for w in LURE_WORDS if w in tokens)
    return hits


def _url_has_dangerous_extension(parsed) -> str | None:
    path = (parsed.path or "").lower()
    match = re.search(r"\.([a-z0-9]+)(?:$|[?#])", path)
    if not match:
        return None

    ext = match.group(1)
    return ext if ext in DANGEROUS_FILE_EXTENSIONS else None


def _count_query_params(raw_query: str) -> int:
    q = (raw_query or "").strip("&?")
    if not q:
        return 0
    return q.count("&") + 1


def _sms_threats(payload: str) -> list[str]:
    p = (payload or "").strip()
    up = p.upper()
    threats: list[str] = []

    if up.startswith(("SMSTO:", "SMS:")):
        threats.append("SMS QR may trigger a prefilled SMS action (social engineering risk).")
        if any(k in p.lower() for k in ["bank", "otp", "verify", "urgent", "money", "transfer", "payment"]):
            threats.append("Smishing-style keywords detected inside SMS payload.")
    return threats


def _tel_threats(payload: str) -> list[str]:
    p = (payload or "").strip().lower()
    threats: list[str] = []

    if p.startswith("tel:"):
        threats.append("TEL QR can initiate a phone call and may be used for scam-call redirection.")
    return threats


def _phone_number_threats(payload: str) -> list[str]:
    p = (payload or "").strip()
    threats: list[str] = []
    if p:
        threats.append("Plain phone number detected; verify before calling or saving.")
    return threats


def _email_threats(payload: str) -> list[str]:
    p = (payload or "").strip()
    up = p.upper()
    threats: list[str] = []

    if p.lower().startswith("mailto:") or up.startswith("MATMSG:"):
        threats.append("EMAIL QR may prefill an email message (phishing / impersonation risk).")
        if any(k in p.lower() for k in ["password", "otp", "verify", "urgent", "invoice", "payment", "bank"]):
            threats.append("Phishing-style keywords detected inside email payload.")
    return threats


def _email_address_threats(payload: str) -> list[str]:
    p = (payload or "").strip()
    threats: list[str] = []
    if p:
        threats.append("Plain email address detected; verify recipient identity before use.")
    return threats


def _vcard_threats(payload: str) -> list[str]:
    up = (payload or "").upper()
    threats: list[str] = []

    if up.startswith("BEGIN:VCARD") or "VCARD" in up:
        threats.append("VCARD QR can import contact data and may hide risky fields.")
        if "URL:" in up or "HTTP" in up:
            threats.append("VCARD contains URL fields; embedded links should be verified before opening.")
    return threats


def _mecard_threats(payload: str) -> list[str]:
    up = (payload or "").upper()
    threats: list[str] = []

    if up.startswith("MECARD:"):
        threats.append("MECARD QR can import contact data and may contain misleading contact details.")
        if "URL:" in up or "HTTP" in up:
            threats.append("MECARD contains URL fields; embedded links should be verified before opening.")
    return threats


def _geo_threats(payload: str) -> list[str]:
    p = (payload or "").strip().lower()
    threats: list[str] = []

    if p.startswith("geo:"):
        threats.append("GEO QR opens a map/location action; verify the location context before opening.")
    return threats


def _deeplink_threats(payload: str) -> list[str]:
    p = (payload or "").strip().lower()
    threats: list[str] = []

    if p.startswith(("intent://", "market://")):
        threats.append("Deep link QR may open an app, app store page, or trigger device actions.")
        if "browser_fallback_url=" in p or "fallback" in p:
            threats.append("Deep link contains fallback/redirect behavior that should be verified.")
    return threats


def _payment_threats(payload: str) -> list[str]:
    p = (payload or "").strip()
    threats: list[str] = []

    if p:
        threats.append("Payment-style QR detected; verify recipient and transaction details before proceeding.")
    return threats


def _verdict_band(score: int) -> str:
    if score >= 85:
        return "CRITICAL"
    if score >= 65:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"


def _recommendation_for_verdict(verdict: str) -> str:
    if verdict == "CRITICAL":
        return "Do not open or execute this QR content. Treat it as malicious until proven otherwise."
    if verdict == "HIGH":
        return "Avoid opening automatically. Verify destination or content through a trusted source first."
    if verdict == "MEDIUM":
        return "Proceed only after manual verification of the destination, sender, and intent."
    return "No strong malicious signal was found, but the content should still be verified before use."


def _combine_rule_and_ml(rule_score: int, ml_score: int, ml_label: str | None) -> int:
    if ml_score <= 0:
        return _clamp(rule_score)

    combined = round((rule_score * 0.65) + (ml_score * 0.35))

    if ml_label == "phishing" and rule_score >= 30:
        combined += 10

    if rule_score >= 75:
        combined = max(combined, rule_score)

    return _clamp(combined)


def _estimate_confidence(findings_count: int, rule_score: int, ml_score: int) -> float:
    confidence = 0.45 + min(findings_count, 6) * 0.05
    if ml_score > 0:
        confidence += abs(ml_score - 50) / 100 * 0.20
    else:
        confidence += min(rule_score, 80) / 100 * 0.15
    return round(min(0.99, confidence), 2)


def _analyze_url(url: str) -> dict:
    findings: list[str] = []
    benign: list[str] = []
    score_breakdown: list[dict] = []
    url_rule_score = 0
    hard_fail = False

    def add_issue(message: str, points: int) -> None:
        nonlocal url_rule_score
        _append_unique(findings, message)
        if points > 0:
            score_breakdown.append({"points": points, "reason": message})
            url_rule_score = _clamp(url_rule_score + points)

    def add_benign(message: str) -> None:
        _append_unique(benign, message)

    candidate = (url or "").strip()
    parsed = _safe_parse_url(candidate)
    scheme = (parsed.scheme or "").lower()
    hostname = _normalize_domain(parsed.hostname)
    raw_path = unquote(parsed.path or "")
    raw_query = unquote(parsed.query or "")
    full_lower = candidate.lower()

    if scheme in DANGEROUS_URL_SCHEMES:
        add_issue(f"Dangerous URL scheme detected: {scheme}:", 45)
        hard_fail = True

    if scheme == "http":
        add_issue("URL uses HTTP instead of HTTPS.", 10)
    elif scheme == "https":
        add_benign("URL uses HTTPS.")
    elif scheme and scheme not in DANGEROUS_URL_SCHEMES:
        add_benign(f"Non-web scheme detected: {scheme}:")

    if scheme not in DANGEROUS_URL_SCHEMES:
        if not hostname:
            add_issue("URL parsing failed or hostname could not be determined.", 25)
        else:
            if _domain_in_set(hostname, RESERVED_DOMAINS):
                add_issue("Reserved/test domain detected (example.com / localhost / similar).", 8)

            if _domain_in_set(hostname, ALLOWLIST_DOMAINS):
                add_benign("Domain belongs to the allowlist (path/query still require review).")

            if _domain_in_set(hostname, SHORTENERS):
                add_issue("URL shortener detected; final destination is hidden.", 24)

            if "xn--" in hostname:
                add_issue("Punycode domain detected (possible homograph / IDN abuse).", 20)

            is_ip_host = _host_is_ip(hostname)

            if is_ip_host:
                add_issue("IP address used as hostname instead of a domain.", 25)
                hard_fail = True
            else:
                dot_count = hostname.count(".")
                if dot_count >= 3:
                    add_issue("Many subdomains detected in hostname.", 8)

                if len(hostname) > 40:
                    add_issue("Hostname is unusually long.", 8)

                if hostname.count("-") >= 3:
                    add_issue("Hostname contains many dashes, which is common in phishing domains.", 8)

                dns_state = _dns_resolves(hostname)
                if dns_state is True:
                    add_benign("Domain resolves in DNS.")
                elif dns_state is False and not _domain_in_set(hostname, RESERVED_DOMAINS):
                    add_issue("Domain did not resolve in DNS.", 8)
                elif dns_state is None:
                    add_benign("DNS lookup skipped.")

    if "@" in (parsed.netloc or ""):
        add_issue("Embedded credentials or '@' obfuscation detected in URL authority.", 20)

    if full_lower.count("http://") + full_lower.count("https://") > 1:
        add_issue("Multiple embedded http/https strings detected (possible redirect or obfuscation).", 12)

    if candidate.count("%") >= 3:
        add_issue("Heavy percent-encoding detected in URL.", 8)

    if len(candidate) > 200:
        add_issue("URL is extremely long.", 15)
    elif len(candidate) > 120:
        add_issue("URL is unusually long.", 8)

    if "//" in raw_path:
        add_issue("Double-slash sequence detected inside path.", 8)

    if _count_query_params(parsed.query) >= 6:
        add_issue("URL contains many query parameters.", 5)

    if re.search(r"(?i)(?:redirect|url|next|target|dest|destination)=", raw_query):
        add_issue("Redirect-like query parameter detected.", 6)

    dangerous_ext = _url_has_dangerous_extension(parsed)
    if dangerous_ext:
        add_issue(f"Suspicious file extension referenced: .{dangerous_ext}", 25)
        hard_fail = True

    lure_hits = _extract_lure_hits(candidate)
    if lure_hits:
        add_issue(f"Suspicious lure words detected in URL: {', '.join(lure_hits)}", 6)

    ml_result = None
    ml_label = None
    ml_score = 0

    if scheme in {"", "http", "https"}:
        if model_exists():
            try:
                ml_result = predict_url(candidate)
                ml_label = str(ml_result.get("label")) if ml_result.get("label") is not None else None
                probability = float(ml_result.get("phishing_probability", 0.0) or 0.0)
                ml_score = _clamp(probability * 100)

                if ml_label == "phishing":
                    add_issue(
                        f"ML flagged URL as phishing (p={probability:.3f}, thr={float(ml_result.get('threshold', 0.5)):.3f}).",
                        0,
                    )
                else:
                    add_benign(f"ML labeled URL as benign (p={probability:.3f}).")
            except Exception as exc:
                add_issue(f"ML prediction failed: {exc}", 8)
        else:
            add_benign("ML model not available; skipped ML URL classification.")
    else:
        add_benign("ML URL classification skipped for non-web scheme.")

    final_url_score = _combine_rule_and_ml(url_rule_score, ml_score, ml_label)
    if hard_fail:
        final_url_score = max(final_url_score, 80)

    return {
        "url": candidate,
        "domain": hostname,
        "scheme": scheme,
        "rule_score": _clamp(url_rule_score),
        "ml_score": _clamp(ml_score),
        "risk_score": _clamp(final_url_score),
        "findings": findings,
        "benign": benign,
        "ml": ml_result,
        "ml_label": ml_label,
        "score_breakdown": score_breakdown,
    }


# -----------------------------
# Main Analyzer
# -----------------------------
async def analyze_qr_payload(payload: str, report_id: str | None = None) -> dict:
    payload = (payload or "").strip()

    findings: list[str] = []
    benign: list[str] = []
    score_breakdown: list[dict] = []
    rule_score = 0
    ml_score = 0

    def add_rule_points(message: str, points: int, source: str) -> None:
        nonlocal rule_score
        _append_unique(findings, message)
        if points > 0:
            score_breakdown.append({"source": source, "points": points, "reason": message})
            rule_score = _clamp(rule_score + points)

    def add_group(messages: list[str], total_points: int, source: str, prefix: str = "") -> None:
        nonlocal rule_score
        if not messages:
            return

        for msg in messages:
            _append_unique(findings, f"{prefix}{msg}" if prefix else msg)

        if total_points > 0:
            score_breakdown.append(
                {
                    "source": source,
                    "points": total_points,
                    "reason": f"{len(messages)} finding(s) from {source}",
                }
            )
            rule_score = _clamp(rule_score + total_points)

    def add_benign(message: str) -> None:
        _append_unique(benign, message)

    if not report_id or not str(report_id).strip():
        report_id = _new_report_id()

    ptype = detect_payload_type(payload)
    _append_unique(findings, f"Payload type: {ptype}")

    pattern_details = scan_for_patterns_detailed(payload)
    if pattern_details:
        for detail in pattern_details:
            add_rule_points(
                f"[PATTERN/{detail['category']}] {detail['message']}",
                int(detail["score"]),
                "pattern",
            )
    else:
        add_benign("No dangerous inline patterns detected in raw payload.")

    extracted_url: str | None = None

    if ptype == "wifi":
        wifi_issues = detect_wifi_threats(payload)
        if wifi_issues:
            add_group(wifi_issues, min(35, 10 * len(wifi_issues)), "wifi", prefix="[WIFI] ")
        else:
            add_benign("Wi-Fi payload present, but no obvious Wi-Fi misconfiguration threat was detected.")

    elif ptype == "sms":
        sms_issues = _sms_threats(payload)
        if sms_issues:
            sms_points = 16 if len(sms_issues) == 1 else 28
            add_group(sms_issues, sms_points, "sms", prefix="[SMS] ")

    elif ptype == "tel":
        tel_issues = _tel_threats(payload)
        if tel_issues:
            add_group(tel_issues, 10, "tel", prefix="[TEL] ")

    elif ptype == "phone_number":
        phone_issues = _phone_number_threats(payload)
        if phone_issues:
            add_group(phone_issues, 4, "phone_number", prefix="[PHONE] ")

    elif ptype == "email":
        email_issues = _email_threats(payload)
        if email_issues:
            email_points = 14 if len(email_issues) == 1 else 22
            add_group(email_issues, email_points, "email", prefix="[EMAIL] ")

    elif ptype == "email_address":
        email_addr_issues = _email_address_threats(payload)
        if email_addr_issues:
            add_group(email_addr_issues, 4, "email_address", prefix="[EMAIL] ")

    elif ptype == "vcard":
        vcard_issues = _vcard_threats(payload)
        if vcard_issues:
            vcard_points = 10 if len(vcard_issues) == 1 else 18
            add_group(vcard_issues, vcard_points, "vcard", prefix="[VCARD] ")
        extracted_url = _extract_url_from_vcard(payload)

    elif ptype == "mecard":
        mecard_issues = _mecard_threats(payload)
        if mecard_issues:
            mecard_points = 10 if len(mecard_issues) == 1 else 18
            add_group(mecard_issues, mecard_points, "mecard", prefix="[MECARD] ")
        extracted_url = _extract_url_from_mecard(payload)

    elif ptype == "geo":
        geo_issues = _geo_threats(payload)
        if geo_issues:
            add_group(geo_issues, 5, "geo", prefix="[GEO] ")

    elif ptype == "deeplink":
        deeplink_issues = _deeplink_threats(payload)
        if deeplink_issues:
            deeplink_points = 14 if len(deeplink_issues) == 1 else 22
            add_group(deeplink_issues, deeplink_points, "deeplink", prefix="[DEEPLINK] ")

    elif ptype == "payment":
        payment_issues = _payment_threats(payload)
        if payment_issues:
            add_group(payment_issues, 12, "payment", prefix="[PAYMENT] ")

    elif ptype == "url":
        extracted_url = payload

    else:
        extracted_url = _extract_first_url_anywhere(payload)

    url_analysis = None
    if extracted_url:
        url_analysis = _analyze_url(extracted_url)

        for item in url_analysis["findings"]:
            _append_unique(findings, f"[URL] {item}")

        for item in url_analysis["benign"]:
            _append_unique(benign, f"[URL] {item}")

        url_rule_contribution = min(65, _clamp(url_analysis["rule_score"] * 0.85))
        if url_rule_contribution > 0:
            score_breakdown.append(
                {
                    "source": "url",
                    "points": url_rule_contribution,
                    "reason": "Aggregated URL lexical/scheme analysis",
                }
            )
            rule_score = _clamp(rule_score + url_rule_contribution)

        ml_score = _clamp(url_analysis["ml_score"])

    ml_label = url_analysis.get("ml_label") if url_analysis else None
    final_score = _combine_rule_and_ml(rule_score, ml_score, ml_label)

    if url_analysis and url_analysis["risk_score"] >= 80:
        final_score = max(final_score, url_analysis["risk_score"])

    verdict = _verdict_band(final_score)
    confidence = _estimate_confidence(len(findings), rule_score, ml_score)

    result = {
        "report_id": report_id,
        "payload": payload,
        "payload_type": ptype,
        "rule_score": _clamp(rule_score),
        "ml_score": _clamp(ml_score),
        "final_score": _clamp(final_score),
        "risk_score": _clamp(final_score),
        "verdict": verdict,
        "confidence": confidence,
        "recommendation": _recommendation_for_verdict(verdict),
        "findings": findings,
        "benign": benign,
        "score_breakdown": score_breakdown,
        "url_analysis": url_analysis,
        "generated_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    }

    result["report_md"] = build_markdown_report(result)
    return result