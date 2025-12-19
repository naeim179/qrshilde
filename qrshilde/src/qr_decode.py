import argparse
import json
from pathlib import Path

import cv2


def decode_qr_from_image(image_path: str) -> list[str]:
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    img = cv2.imread(str(p))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    det = cv2.QRCodeDetector()

    # Try multi first
    ok, decoded_info, points, _ = det.detectAndDecodeMulti(img)
    results = []

    if ok and decoded_info:
        results = [x for x in decoded_info if x]
    else:
        txt, pts, _ = det.detectAndDecode(img)
        if txt:
            results = [txt]

    return results


def main():
    ap = argparse.ArgumentParser(description="Decode QR code from an image.")
    ap.add_argument("image", help="Path to QR image (png/jpg)")
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    args = ap.parse_args()

    results = decode_qr_from_image(args.image)

    if args.json:
        print(json.dumps({"image": args.image, "decoded": results}, ensure_ascii=False, indent=2))
    else:
        if not results:
            print("No QR code detected.")
        else:
            for i, r in enumerate(results, 1):
                print(f"[{i}] {r}")


if __name__ == "__main__":
    main()
