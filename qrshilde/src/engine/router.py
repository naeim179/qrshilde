def should_use_groq(content_type: str, payload: str) -> bool:
    ct = (content_type or "").lower()
    text = (payload or "").strip()

    if ct in {"phone", "geo"}:
        return False

    if ct in {"url", "wifi", "sms", "email", "vcard"}:
        return True

    if ct == "unknown" or len(text) > 80:
        return True

    return False
