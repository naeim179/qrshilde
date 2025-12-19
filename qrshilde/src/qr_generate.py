import argparse
from pathlib import Path

import qrcode


def generate_qr(text: str, out_path: str, box_size: int = 10, border: int = 4, ec_level: str = "M") -> str:
    ec_map = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }
    ec = ec_map.get(ec_level.upper(), qrcode.constants.ERROR_CORRECT_M)

    qr = qrcode.QRCode(error_correction=ec, box_size=box_size, border=border)
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return str(out)


def main():
    ap = argparse.ArgumentParser(description="Generate a QR code image from text/payload.")
    ap.add_argument("--text", required=True, help="Text/payload to encode")
    ap.add_argument("--out", default="out.png", help="Output image path (png)")
    ap.add_argument("--box", type=int, default=10, help="Box size")
    ap.add_argument("--border", type=int, default=4, help="Border size")
    ap.add_argument("--ec", default="M", choices=["L", "M", "Q", "H"], help="Error correction level")
    args = ap.parse_args()

    out = generate_qr(args.text, args.out, args.box, args.border, args.ec)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
