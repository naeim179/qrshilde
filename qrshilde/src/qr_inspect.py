import argparse
import json
import re
from urllib.parse import urlparse


def classify_payload(text: str) -> dict:
    t = (text or "").strip()

    info = {"type": "unknown", "text": t, "details": {}}

    if not t:
        info["type"] = "empty"
        return info

    up = t.upper()

    # URL
    if re.match(r"^https?://", t, re.I):
        info["type"] = "url"
        u = urlparse(t)
        info["details"] = {"scheme": u.scheme, "host": u.netloc, "path": u.path, "query": u.query}
        return info

    # WIFI
    if up.startswith("WIFI:"):
        info["type"] = "wifi"
        # Simple parse: WIFI:T:WPA;S:SSID;P:PASS;;
        ssid = re.search(r"(?:^|;)S:([^;]*)", t)
        auth = re.search(r"(?:^|;)T:([^;]*)", t)
        pwd = re.search(r"(?:^|;)P:([^;]*)", t)
        hidden = re.search(r"(?:^|;)H:([^;]*)", t)
        info["details"] = {
            "ssid": ssid.group(1) if ssid else None,
            "auth": auth.group(1) if auth else None,
            "password_present": bool(pwd and pwd.group(1)),
            "hidden": hidden.group(1) if hidden else None,
        }
        return info

    # VCARD
    if up.startswith("BEGIN:VCARD"):
        info["type"] = "vcard"
        return info

    # SMS
    if up.startswith("SMSTO:") or up.startswith("SMS:"):
        info["type"] = "sms"
        return info

    # MAIL
    if up.startswith("MAILTO:") or up.startswith("MATMSG:"):
        info["type"] = "email"
        return info

    # TEL
    if up.startswith("TEL:"):
        info["type"] = "phone"
        info["details"] = {"number": t[4:]}
        return info

    # GEO
    if up.startswith("GEO:"):
        info["type"] = "geo"
        return info

    return info


def main():
    ap = argparse.ArgumentParser(description="Inspect/classify QR decoded text payload.")
    ap.add_argument("--text", required=True, help="Decoded QR text")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    args = ap.parse_args()

    result = classify_payload(args.text)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Type: {result['type']}")
        if result["details"]:
            for k, v in result["details"].items():
                print(f"- {k}: {v}")


if __name__ == "__main__":
    main()
