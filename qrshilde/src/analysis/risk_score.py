def basic_risk_score(meta: dict) -> int:
    """
    سكورنغ بسيط كبداية (0-100).
    لاحقاً نقدر ندمج AI يعطي رقم أدق.
    """
    qr_type = meta.get("qr_type", "TEXT")
    score = 10

    if qr_type in ("TEXT",):
        return 5

    if qr_type in ("URL", "URL_CANDIDATE"):
        score = 40
        domain = meta.get("domain", "")
        # دومينات شكلها مش مريح
        if any(c.isdigit() for c in domain):
            score += 15
        if "-" in domain:
            score += 10
        if len(domain) > 20:
            score += 10

    if qr_type == "WIFI":
        score = 50

    if qr_type in ("SMS", "PHONE"):
        score = 60

    if qr_type == "VCARD":
        score = 45

    # نخلي السكور بين 0 و 100
    return max(0, min(score, 100))
