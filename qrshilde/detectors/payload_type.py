import re


URL_RE = re.compile(
    r"^(?:(?:https?://)|(?:www\.))",
    re.IGNORECASE,
)

URL_ANYWHERE_RE = re.compile(
    r"(?i)\b(?:https?://|www\.)[^\s<>'\"]+"
)

EMAIL_RE = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    re.IGNORECASE,
)

PHONE_RE = re.compile(
    r"^\+?[0-9][0-9\-\s\(\)]{5,}$"
)


def detect_payload_type(payload: str) -> str:
    p = (payload or "").strip()
    if not p:
        return "empty"

    up = p.upper()
    low = p.lower()

    # URL / web link
    if URL_RE.match(p):
        return "url"

    # Common QR action schemes
    if up.startswith("WIFI:"):
        return "wifi"

    if up.startswith(("SMSTO:", "SMS:")):
        return "sms"

    if low.startswith("tel:"):
        return "tel"

    if low.startswith("mailto:") or up.startswith("MATMSG:"):
        return "email"

    # Contact cards
    if up.startswith("BEGIN:VCARD"):
        return "vcard"

    if up.startswith("MECARD:"):
        return "mecard"

    # Calendar event
    if up.startswith("BEGIN:VEVENT"):
        return "event"

    # Geo location
    if low.startswith("geo:"):
        return "geo"

    # App / mobile deep links
    if low.startswith(("intent://", "market://")):
        return "deeplink"

    # EPC / payment-like / banking-ish payloads can be extended later
    if up.startswith("SPC") or "BCD\n" in up:
        return "payment"

    # Email address only
    if EMAIL_RE.match(p):
        return "email_address"

    # Phone number only
    if PHONE_RE.match(p):
        return "phone_number"

    # Text containing an embedded URL
    if URL_ANYWHERE_RE.search(p):
        return "text_with_url"

    return "text"