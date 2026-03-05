import argparse
import sys

from . import qr_decode, qr_analyze


def run_script_main(mod, argv):
    """Call module.main() after setting sys.argv the way the script expects."""
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

    # Decode QR from image
    d = sub.add_parser("decode", help="Decode QR from image")
    d.add_argument("image", help="Path to image (png/jpg)")
    d.add_argument("rest", nargs=argparse.REMAINDER, help="Extra args")

    # Analyze payload (text or image path based on qr_analyze implementation)
    a = sub.add_parser("analyze", help="Analyze QR content (Text OR Image)")
    a.add_argument("target", help="Image path OR decoded text")
    a.add_argument("-o", "--out", default="report.md", help="Output report file")
    a.add_argument("rest", nargs=argparse.REMAINDER, help="Extra args")

    args = p.parse_args()

    if args.cmd == "decode":
        run_script_main(qr_decode, [args.image] + args.rest)

    elif args.cmd == "analyze":
        # qr_analyze expects --text and --out (حسب اللي عندك)
        run_script_main(qr_analyze, ["--text", args.target, "--out", args.out] + args.rest)


if __name__ == "__main__":
    main()