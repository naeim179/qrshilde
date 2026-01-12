import argparse
import sys

# استيراد الملفات الفرعية
from . import qr_decode, qr_generate, qr_analyze, qr_inspect


def run_script_main(mod, argv):
    """
    Call module.main() after setting sys.argv the way the script expects.
    """
    if not hasattr(mod, "main"):
        raise SystemExit(f"{mod.__name__} has no main()")
    old = sys.argv[:]
    try:
        sys.argv = [mod.__name__] + argv
        mod.main()
    finally:
        sys.argv = old


def main():
    p = argparse.ArgumentParser(prog="qrshilde")
    sub = p.add_subparsers(dest="cmd", required=True)

    # 1. Decode Command
    d = sub.add_parser("decode", help="Decode QR from image")
    d.add_argument("image", help="Path to image (png/jpg)")
    d.add_argument("rest", nargs=argparse.REMAINDER, help="Extra args forwarded to qr_decode.py")

    # 2. Generate Command
    g = sub.add_parser("gen", help="Generate QR image")
    g.add_argument("text", help="Text/payload")
    g.add_argument("-o", "--out", default="out.png", help="Output image path")
    g.add_argument("rest", nargs=argparse.REMAINDER, help="Extra args forwarded to qr_generate.py")

    # 3. Analyze Command (هنا كان التعديل)
    a = sub.add_parser("analyze", help="Analyze decoded QR content")
    a.add_argument("target", help="Image path OR decoded text (depends on your script)")
    a.add_argument("rest", nargs=argparse.REMAINDER, help="Extra args forwarded to qr_analyze.py")

    # 4. Inspect Command
    i = sub.add_parser("inspect", help="Inspect QR payload / classify")
    i.add_argument("target", help="Image path OR decoded text (depends on your script)")
    i.add_argument("rest", nargs=argparse.REMAINDER, help="Extra args forwarded to qr_inspect.py")

    args = p.parse_args()

    # --- التنفيذ ---

    if args.cmd == "decode":
        run_script_main(qr_decode, [args.image] + args.rest)

    elif args.cmd == "gen":
        run_script_main(qr_generate, [args.text, "-o", args.out] + args.rest)

    elif args.cmd == "analyze":
        # ✅ التعديل هنا: أضفنا "--text" ليتم تمريرها للمحلل
        run_script_main(qr_analyze, ["--text", args.target] + args.rest)

    elif args.cmd == "inspect":
        run_script_main(qr_inspect, [args.target] + args.rest)


if __name__ == "__main__":
    main()