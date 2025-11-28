from qrshilde.src.ai.analyzer import analyze_qr_payload
from qrshilde.src.utils.extractor import extract_metadata
import argparse


def main():
    parser = argparse.ArgumentParser(description="Analyze QR content with AI & local heuristics.")
    parser.add_argument(
        "--text",
        help="Raw decoded QR text to analyze",
    )
    parser.add_argument(
        "--out",
        help="Optional path to save markdown report",
        default=None,
    )

    args = parser.parse_args()

    if not args.text:
        print("[!] Please provide --text with decoded QR content.")
        return

    analysis = analyze_qr_payload(args.text)
    report_md = build_markdown_report(analysis)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"[+] Report saved to {args.out}")
    else:
        print(report_md)


if __name__ == "__main__":
    main()
