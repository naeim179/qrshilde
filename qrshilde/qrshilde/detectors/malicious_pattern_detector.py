import re


def _extract_wifi_field(payload: str, key: str) -> str | None:
    raw = (payload or "").strip()
    if not raw:
        return None

    if raw.upper().startswith("WIFI:"):
        raw = raw[5:]

    pattern = rf"(?:^|;){re.escape(key)}:((?:\\.|[^;])*)"
    match = re.search(pattern, raw, flags=re.IGNORECASE)
    if not match:
        return None

    value = match.group(1).strip()
    # ✅ ترتيب صح: \\ أول شي عشان ما نكسر الـ escape sequences
    value = value.replace(r"\\", "\\").replace(r"\;", ";").replace(r"\:", ":")
    return value


def detect_wifi_threats(payload: str) -> list[str]:
    threats: list[str] = []

    raw = (payload or "").strip()
    if not raw.upper().startswith("WIFI:"):
        return threats

    encryption = (_extract_wifi_field(raw, "T") or "").strip()
    ssid        = (_extract_wifi_field(raw, "S") or "").strip()
    password    = (_extract_wifi_field(raw, "P") or "").strip()
    hidden      = (_extract_wifi_field(raw, "H") or "").strip().lower()

    enc_upper = encryption.upper()

    if not ssid:
        threats.append("Wi-Fi payload does not specify an SSID (malformed or suspicious).")

    if enc_upper == "NOPASS":
        threats.append("Unsecured Wi-Fi network detected (no password).")
        if password:
            threats.append("Inconsistent payload: NOPASS set but password field is present.")

    elif enc_upper == "":
        threats.append("Wi-Fi encryption type is missing.")
        if password:
            threats.append("Wi-Fi payload includes a password but no encryption type.")

    elif enc_upper == "WEP":
        threats.append("Weak Wi-Fi encryption: WEP is obsolete and easily broken.")
        if not password:
            threats.append("WEP Wi-Fi payload is missing a password/key.")
        elif len(password) < 8:
            threats.append("WEP password/key is very short.")

    elif enc_upper in ("WPA", "WPA2", "WPA3"):
        if not password:
            threats.append(f"{enc_upper} Wi-Fi payload is missing a password.")
        elif len(password) < 8:
            threats.append(f"{enc_upper} Wi-Fi password is too short (minimum 8 chars).")
        elif len(password) < 10:
            threats.append("Wi-Fi password is relatively weak/short.")

    else:
        threats.append(f"Unknown Wi-Fi encryption type: '{encryption}'")

    if hidden == "true":
        threats.append("Hidden Wi-Fi network detected; can be abused in Evil Twin attacks.")

    return threats