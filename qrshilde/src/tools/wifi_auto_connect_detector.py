import re

def detect_wifi_threats(payload: str):
    """
    تحليل رموز WIFI QR
    """
    threats = []
    
    if not payload.startswith("WIFI:"):
        return []

    encryption_match = re.search(r"T:([^;]+)", payload)
    encryption = encryption_match.group(1) if encryption_match else "unknown"

    if encryption.lower() == "nopass" or encryption == "":
        threats.append("Unsecured Wi-Fi Network (No Password) - High Risk.")

    if encryption.upper() == "WEP":
        threats.append("Weak Encryption (WEP) - Easily Hacked.")

    if "H:true" in payload.lower():
        threats.append("Hidden Network - Often used in 'Evil Twin' attacks.")

    return threats
