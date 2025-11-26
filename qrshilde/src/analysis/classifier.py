from urllib.parse import urlparse


def guess_qr_type(payload: str) -> str:
    """
    يحاول يحدد نوع الـ QR من النص:
    - URL
    - WIFI
    - SMS
    - TEL
    - VCARD
    - TEXT
    وهكذا...
    """
    text = payload.strip().upper()

    if text.startswith("WIFI:"):
        return "WIFI"
    if text.startswith("SMSTO:"):
        return "SMS"
    if text.startswith("TEL:"):
        return "PHONE"
    if text.startswith("BEGIN:VCARD"):
        return "VCARD"

    # Check if it looks like a URL
    lowered = payload.strip().lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        return "URL"

    # محاولة بسيطة لتحليل URL بدون البروتوكول
    if "://" not in lowered:
        if "." in lowered and " " not in lowered:
            # ممكن يكون دومين زي example.com/login
            return "URL_CANDIDATE"

    return "TEXT"


def extract_basic_meta(payload: str) -> dict:
    """
    يرجع معلومات بسيطة عن المحتوى تفيد AI و الـ Risk scoring.
    """
    qr_type = guess_qr_type(payload)
    meta: dict = {"qr_type": qr_type}

    if qr_type in ("URL", "URL_CANDIDATE"):
        url = payload.strip()
        if not url.lower().startswith(("http://", "https://")):
            url = "http://" + url
        parsed = urlparse(url)
        meta["domain"] = parsed.netloc
        meta["path"] = parsed.path or "/"
        meta["scheme"] = parsed.scheme

    return meta
