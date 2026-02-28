import re

def detect_wifi_threats(payload: str):
    threats = []

    if not payload.startswith("WIFI:"):
        return []

    encryption_match = re.search(r"T:([^;]+)", payload)
    encryption = encryption_match.group(1) if encryption_match else "unknown"

    if encryption.lower() in ("nopass", ""):
        threats.append("Unsecured Wi-Fi Network (No Password) - High Risk.")

    if encryption.upper() == "WEP":
        threats.append("Weak Encryption (WEP) - Easily Hacked.")

    # ✅ fix: lower-case compare
    if "h:true" in payload.lower():
        threats.append("Hidden Network - Often used in 'Evil Twin' attacks.")

    return threats