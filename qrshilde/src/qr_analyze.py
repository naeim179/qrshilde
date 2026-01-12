#D:\github-projects\qrshilde\qrshilde\src\qr_analyze.py
import argparse
from pathlib import Path

from qrshilde.src.ai.analyzer import analyze_qr_payload


def main():
    parser = argparse.ArgumentParser(
        description="Analyze QR code text payload and generate a security report."
    )

    parser.add_argument(
        "--text",
        type=str,
        required=True,
        help="QR text content (decoded).",
    )

    parser.add_argument(
        "--out",
        type=str,
        default="report.md",
        help="Output Markdown report file.",
    )

    args = parser.parse_args()
    qr_text = args.text
    out_file = Path(args.out)

    print("[+] Analyzing QR payload...")
    result = analyze_qr_payload(qr_text)

    report_md = result["report_md"]
    out_file.write_text(report_md, encoding="utf-8")
    print(f"[+] Report saved to {out_file}")


if __name__ == "__main__":
    main()
