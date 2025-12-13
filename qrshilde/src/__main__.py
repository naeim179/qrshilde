import argparse
from .qr_decode import decode_qr_from_image  # اذا اسم الدالة مختلف خبرني
from .qr_generate import generate_qr         # اذا اسمها مختلف خبرني

def main():
    p = argparse.ArgumentParser(prog="qrshilde")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("decode", help="Decode QR from image")
    d.add_argument("image", help="Path to image (png/jpg)")

    g = sub.add_parser("gen", help="Generate QR image")
    g.add_argument("text", help="Text/payload")
    g.add_argument("-o", "--out", default="out.png", help="Output image path")

    args = p.parse_args()

    if args.cmd == "decode":
        print(decode_qr_from_image(args.image))
    elif args.cmd == "gen":
        generate_qr(args.text, args.out)
        print(f"Saved: {args.out}")

if __name__ == "__main__":
    main()
