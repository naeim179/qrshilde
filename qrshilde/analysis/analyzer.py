import ipaddress
from urllib.parse import urlparse

from qrshilde.threat_memory import lookup_known_indicator, save_analysis_result

SHORTENERS = {"bit.ly", "t.co", "tinyurl.com", "goo.gl"}
SUSPICIOUS_TLDS = [".xyz", ".top", ".tk", ".ml"]

PHISHING_KEYWORDS = [
    "login", "verify", "secure", "account", "update",
    "paypal", "bank", "password", "confirm"
]

DANGEROUS_SCHEMES = {"javascript", "data", "file", "vbscript"}


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
        add("Dangerous scheme detected", 70)
        hard_fail = True

    if _is_ip(hostname):
        add("IP address used instead of domain", 45)
        hard_fail = True

    phishing_hits = sum(1 for w in PHISHING_KEYWORDS if w in url_lower)

    if phishing_hits > 0:
        add(f"Phishing keywords detected ({phishing_hits})", 25)

        if phishing_hits >= 2:
            add("Multiple phishing indicators", 20)

    if "@" in url:
        add("Obfuscated URL using @ trick", 40)
        hard_fail = True

    if any(s in url_lower for s in SHORTENERS):
        add("Shortened URL detected", 35)

    tld_flag = any(hostname.endswith(tld) for tld in SUSPICIOUS_TLDS)
    if tld_flag:
        add("Suspicious domain extension", 30)

    # 🔥 combo attacks
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

    # 🔥 MEMORY CHECK
    memory = lookup_known_indicator(payload)

    if memory:
        findings.append(f"[MEMORY] {memory['message']}")

        findings.append(
            f"[HISTORY] Seen {memory['seen_count']} time(s), last verdict: {memory['last_verdict']}"
        )

        if memory["match_type"] == "exact_payload":
            score = max(score, 80)
        elif memory["match_type"] == "domain":
            score = max(score, 65)

    # 🔴 javascript
    if payload.lower().startswith("javascript:"):
        add("JavaScript injection detected", 70)

    # 🔴 WIFI
    elif payload.startswith("WIFI:"):
        add("WiFi auto-connect QR", 30)

    # 🔴 URL
    elif payload.startswith("http") or payload.startswith("www."):
        url_result = _analyze_url(payload)
        score += url_result["points"]
        findings.extend(url_result["findings"])

    # 🔴 text
    else:
        if any(word in payload.lower() for word in PHISHING_KEYWORDS):
            add("Phishing keywords detected in payload", 20)

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

    # 🔥 SAVE TO MEMORY
    try:
        save_analysis_result(result)
    except:
        pass

    return result