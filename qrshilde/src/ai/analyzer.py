import datetime
import os
from urllib.parse import urlparse

from qrshilde.src.ai.openai_client import ask_model, format_ai_analysis
from qrshilde.src.tools.malicious_pattern_detector import scan_for_patterns
from qrshilde.src.tools.wifi_auto_connect_detector import detect_wifi_threats
from qrshilde.src.tools.payload_type import detect_payload_type
from qrshilde.src.ml.url_model import predict_url, model_exists


# Confidence zones for ML probability (p)
HIGH_CONF = 0.85   # confident malicious
LOW_CONF = 0.15    # confident benign

# Domains we treat as trusted/known for demo + reducing false positives
ALLOWLIST_DOMAINS = {
    "example.com",
    "github.com",
    "google.com",
    "wikipedia.org",
    "microsoft.com",
    "paypal.com",
}

# Brands we consider for impersonation heuristics
BRANDS = {
    "paypal": {"paypal.com"},
    "google": {"google.com"},
    "microsoft": {"microsoft.com"},
    "apple": {"apple.com"},
    "netflix": {"netflix.com"},
    "binance": {"binance.com"},
}

LURE_WORDS = ["login", "verify", "secure", "update", "account", "support", "confirm"]


async def capture_screenshot(url, report_id):
    """Capture screenshot (best-effort)."""
    try:
        from playwright.async_api import async_playwright

        screenshot_name = f"evidence_{report_id}.png"
        screenshot_path = os.path.join("static", "uploads", screenshot_name)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=10000, wait_until="domcontentloaded")
            await page.screenshot(path=screenshot_path)
            await browser.close()

        return f"/static/uploads/{screenshot_name}"
    except Exception as e:
        print(f"[⚠️] Screenshot skipped: {e}")
        return None


def _extract_domain(url: str) -> str | None:
    try:
        u = url if "://" in url else "http://" + url
        host = urlparse(u).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host or None
    except Exception:
        return None


def _extract_path(url: str) -> str:
    try:
        u = url if "://" in url else "http://" + url
        return (urlparse(u).path or "").lower()
    except Exception:
        return ""


def url_heuristics(payload: str):
    """
    Strong heuristics for phishing-like URLs (brand-in-domain + lure words, http).
    Returns: (score_add, findings_list)
    """
    findings = []
    score = 0

    host = (_extract_domain(payload) or "").lower()
    path = (_extract_path(payload) or "").lower()

    # 1) Brand impersonation in domain
    for brand, legit_domains in BRANDS.items():
        brand_in_host = brand in host
        is_legit = any(host == d or host.endswith("." + d) for d in legit_domains)

        if brand_in_host and not is_legit:
            findings.append(f"URL Heuristic: brand-in-domain impersonation ({brand})")
            score += 40

            if any(w in host for w in LURE_WORDS) or any(w in path for w in LURE_WORDS):
                findings.append("URL Heuristic: lure words detected (login/verify/secure/...)")
                score += 25

    # 2) HTTP without TLS
    if payload.strip().lower().startswith("http://"):
        findings.append("URL Heuristic: HTTP without TLS")
        score += 10

    # 3) Very long / suspicious structure (lightweight)
    if len(payload) >= 120:
        findings.append("URL Heuristic: very long URL (possible obfuscation)")
        score += 10

    return score, findings


def sms_heuristics(payload: str):
    """
    Smishing keyword heuristics.
    Returns: (score_add, findings_list)
    """
    findings = []
    score = 0
    low = (payload or "").lower()

    # consider SMSTO / SMS formats
    if low.startswith(("smsto:", "sms:")):
        findings.append("SMS QR: May trigger composing/sending an SMS (social engineering risk).")
        score += 10

        if any(k in low for k in ["otp", "bank", "urgent", "verify", "password", "transfer", "payment", "invoice"]):
            findings.append("SMS Heuristic: smishing keywords detected (otp/bank/urgent/verify/...)")
            score += 35

    return score, findings


def tel_heuristics(payload: str):
    findings = []
    score = 0
    low = (payload or "").strip().lower()
    if low.startswith("tel:"):
        findings.append("TEL QR: Can initiate a phone call—used in vishing/toll fraud.")
        score += 15
    return score, findings


def vcard_heuristics(payload: str):
    findings = []
    score = 0
    up = (payload or "").upper()
    if up.startswith("BEGIN:VCARD") or "VCARD" in up:
        findings.append("VCARD QR: Can import contact data—may hide malicious URLs in fields.")
        score += 10
        if "URL:" in up or "HTTP" in up:
            findings.append("VCARD contains URL fields—verify before opening embedded links.")
            score += 20
    return score, findings


async def analyze_qr_payload(payload, report_id):
    payload = payload or ""

    findings = []
    risk_score = 0
    evidence_img = None

    # 0) detect payload type
    ptype = detect_payload_type(payload)
    findings.append(f"Payload type: {ptype}")

    # 1) allowlist reduce false positives
    allowlisted = False
    if ptype == "url":
        host = _extract_domain(payload)
        if host and host in ALLOWLIST_DOMAINS:
            allowlisted = True
            findings.append(f"Allowlist: trusted/known domain detected ({host})")
            risk_score -= 20

    # 2) always scan known patterns (regex attacks)
    pattern_issues = scan_for_patterns(payload)
    if pattern_issues:
        findings.extend(pattern_issues)
        risk_score += 40

    # 3) type-specific rules
    if ptype == "wifi":
        wifi_issues = detect_wifi_threats(payload)
        if wifi_issues:
            findings.extend(wifi_issues)
            risk_score += 35

    if ptype == "sms":
        s, f = sms_heuristics(payload)
        if f:
            findings.extend(f)
            risk_score += s

    if ptype == "tel":
        s, f = tel_heuristics(payload)
        if f:
            findings.extend(f)
            risk_score += s

    if ptype == "vcard":
        s, f = vcard_heuristics(payload)
        if f:
            findings.extend(f)
            risk_score += s

    if ptype == "deeplink":
        findings.append("Deep link QR: May open apps directly (higher risk if unexpected).")
        risk_score += 20

    # 4) URL heuristics (override ML mistakes)
    if ptype == "url":
        hs, hf = url_heuristics(payload)
        if hf:
            findings.extend(hf)
            risk_score += hs

    # 5) ML URL model
    ml_result = None
    ml_confident = False

    if ptype == "url" and model_exists():
        try:
            ml_result = predict_url(payload)
            p = float(ml_result.get("phishing_probability", 0.0))
            t_mal = float(ml_result.get("threshold", 0.31))

            # 3-zone logic
            if p >= HIGH_CONF:
                findings.append(f"ML: High malicious probability ({p:.2f})")
                risk_score += 60
                ml_confident = True

            elif p <= LOW_CONF:
                findings.append(f"ML: High benign confidence ({p:.2f})")
                ml_confident = True

            else:
                if p >= t_mal:
                    findings.append(f"ML: Gray-zone suspicious ({p:.2f})")
                    risk_score += 25
                else:
                    findings.append(f"ML: Gray-zone likely benign ({p:.2f})")
                    risk_score += 5

        except Exception as e:
            findings.append(f"ML error: {e}")

    # ✅ IMPORTANT: If heuristics already raised suspicion, do NOT trust ML benign as final
    if risk_score >= 35:
        ml_confident = False

    # 6) Screenshot only if it adds value
    if ptype == "url" and (not ml_confident):
        ml_suspicious = False
        try:
            if ml_result:
                p = float(ml_result.get("phishing_probability", 0.0))
                t = float(ml_result.get("threshold", 0.31))
                ml_suspicious = (p >= t)
        except Exception:
            ml_suspicious = False

        if (not allowlisted) and (risk_score >= 35 or ml_suspicious):
            print("[*] Capturing screenshot for evidence...")
            evidence_img = await capture_screenshot(payload, report_id)

    # 7) AI fallback only when needed
    need_llm = (ptype != "url") or (not model_exists()) or (not ml_confident)

    if need_llm:
        print("[*] Fetching AI Analysis (fallback/uncertain)...")
        ai_json = ask_model(payload)  # returns dict JSON or None
        ai_opinion = format_ai_analysis(ai_json)
    else:
        ai_opinion = "AI skipped (ML confident)."

    # 8) clamp + category
    risk_score = max(0, min(int(risk_score), 100))
    category = "MALICIOUS" if risk_score >= 70 else "SUSPICIOUS" if risk_score >= 35 else "SAFE"

    return {
        "category": category,
        "risk_score": risk_score,
        "findings": findings,
        "ai_analysis": ai_opinion,
        "payload": payload,
        "evidence_img": evidence_img,
        "ml_result": ml_result,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }