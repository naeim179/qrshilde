import ipaddress
from urllib.parse import urlparse

SHORTENERS = {"bit.ly", "t.co", "tinyurl.com", "goo.gl"}
SUSPICIOUS_TLDS = [".xyz", ".top", ".tk", ".ml"]

PHISHING_KEYWORDS = [
    "login", "verify", "secure", "account", "update",
    "paypal", "bank", "password", "confirm"
]

DANGEROUS_SCHEMES = {"javascript", "data", "file", "vbscript"}

SPOOF_PATTERNS = ["paypa1", "g00gle", "faceb00k"]


def _clamp(v):
    return max(0, min(100, int(v)))


def _is_ip(host):
    try:
        ipaddress.ip_address(host)
        return True
    except:
        return False


# =========================
# URL ANALYSIS
# =========================
def _analyze_url(url: str):
    findings = []
    points = 0
    hard_fail = False

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    scheme = parsed.scheme.lower()
    url_lower = url.lower()

    def add(msg, pts):
        nonlocal points
        findings.append(msg)
        points += pts

    if scheme in DANGEROUS_SCHEMES:
        add("Dangerous scheme detected", 80)
        hard_fail = True

    if scheme != "https":
        add("Non-HTTPS URL", 25)

    if _is_ip(hostname):
        add("IP address used instead of domain", 45)
        hard_fail = True

    phishing_hits = sum(1 for w in PHISHING_KEYWORDS if w in url_lower)

    if phishing_hits > 0:
        add(f"Phishing keywords detected ({phishing_hits})", 25)

        if phishing_hits >= 2:
            add("Multiple phishing indicators", 20)

    if any(p in hostname for p in SPOOF_PATTERNS):
        add("Possible domain spoofing", 50)
        hard_fail = True

    if "@" in url:
        add("Obfuscated URL using @ trick", 40)
        hard_fail = True

    if any(s in url_lower for s in SHORTENERS):
        add("Shortened URL detected", 35)

    tld_flag = any(hostname.endswith(tld) for tld in SUSPICIOUS_TLDS)
    if tld_flag:
        add("Suspicious domain extension", 30)

    if phishing_hits > 0 and tld_flag:
        add("Phishing + suspicious domain combo", 30)
        hard_fail = True

    if phishing_hits > 0 and "@" in url:
        add("Phishing + obfuscation combo", 30)
        hard_fail = True

    if len(url) > 120:
        add("Very long URL", 10)

    if url_lower.count("http") > 1:
        add("Multiple embedded URLs", 15)

    if hard_fail:
        points = max(points, 80)

    return {"findings": findings, "points": points}


# =========================
# MAIN ANALYZER
# =========================
async def analyze_qr_payload(payload: str):
    payload = (payload or "").strip()

    findings = []
    score = 0

    def add(msg, pts):
        nonlocal score
        findings.append(msg)
        score += pts

    lower = payload.lower()

    # 🔴 dangerous schemes
    if any(lower.startswith(s + ":") for s in DANGEROUS_SCHEMES):
        add("Dangerous scheme detected", 80)

    elif lower.startswith("sms:"):
        add("SMS trigger detected", 60)

    elif lower.startswith("tel:"):
        add("Phone call trigger detected", 50)

    elif payload.startswith("WIFI:"):
        add("WiFi auto-connect QR", 60)

        if "p:12345678" in lower:
            add("Weak WiFi password", 20)

    elif payload.startswith("http") or payload.startswith("www."):
        url_result = _analyze_url(payload)
        score += url_result["points"]
        findings.extend(url_result["findings"])

    else:
        if any(word in lower for word in PHISHING_KEYWORDS):
            add("Phishing keywords detected in payload", 20)

    # 🔥 boost
    if len(findings) >= 3:
        score += 15

    final_score = _clamp(score)

    if final_score >= 70:
        verdict = "HIGH"
    elif final_score >= 40:
        verdict = "MEDIUM"
    else:
        verdict = "LOW"

    result = {
        "payload": payload,
        "risk_score": final_score,
        "final_score": final_score,
        "verdict": verdict,
        "findings": findings,
        "confidence": round(min(0.95, 0.5 + final_score / 200), 2),
    }

    return result