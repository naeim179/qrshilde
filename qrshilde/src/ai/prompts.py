QR_ANALYSIS_SYSTEM_PROMPT = """
You are a cybersecurity expert specialized in QR code attacks.
You receive already-decoded QR content and metadata.
Your job:
- Identify the type of QR (URL, Wi-Fi, SMS, vCard, payment, app deep link, etc.)
- Classify the attack type if malicious (phishing, QRLjacking, rogue Wi-Fi, vCard injection, etc.)
- Estimate risk level: LOW / MEDIUM / HIGH / CRITICAL
- Explain why in clear points
- Provide practical recommendations in bullet points
Answer in concise English suitable for a security report.
"""

def build_qr_analysis_prompt(payload: str, meta: dict | None = None) -> str:
    """
    يبني البرومبت اللي راح يروح للموديل.
    meta ممكن تحتوي نوع QR لو إحنا عرفناه من الكود (URL, WIFI, SMS...)
    """
    meta_text = ""
    if meta:
        meta_lines = [f"{k}: {v}" for k, v in meta.items()]
        meta_text = "QR Metadata:\n" + "\n".join(meta_lines) + "\n\n"

    prompt = (
        QR_ANALYSIS_SYSTEM_PROMPT
        + "\n\n"
        + meta_text
        + "QR Decoded Content:\n"
        + payload
        + "\n\nProvide:\n"
        + "1) Classification (type + attack type if any)\n"
        + "2) Risk level\n"
        + "3) Reasons\n"
        + "4) Recommendations\n"
    )
    return prompt
