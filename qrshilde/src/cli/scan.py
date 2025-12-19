import argparse
from qrshilde.src.qr_decode import decode_qr_from_image
from qrshilde.src.engine.pipeline import analyze_payload

def main():
    ap = argparse.ArgumentParser(description="QRShilde unified scanner + security classifier")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--image", help="Path to QR image")
    g.add_argument("--text", help="Decoded QR text payload")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    args = ap.parse_args()

    if args.image:
        payloads = decode_qr_from_image(args.image)
    else:
        payloads = [args.text]

    for payload in payloads:
        res = analyze_payload(payload)
        if args.json:
            import json
            print(json.dumps(res.__dict__, ensure_ascii=False, indent=2))
        else:
            print(f"TYPE: {res.content_type}")
            print(f"RISK: {res.risk_level} ({res.risk_score}/100)")
            print(f"ACTION: {res.recommended_action}")
            if res.reasons:
                print("REASONS:")
                for r in res.reasons:
                    print(f"- {r}")
            print("-" * 40)

if __name__ == "__main__":
    main()
