import asyncio
import sys
from pathlib import Path

from qrshilde.analysis.analyzer import analyze_qr_payload


def _print_usage() -> None:
    print("Usage:")
    print('  python -m qrshilde analyze "<payload>"')
    print('  python -m qrshilde analyze-file "<path_to_text_file>"')


async def _run_analyze(payload: str) -> int:
    result = await analyze_qr_payload(payload)

    print("--------------------------------------------------")
    print("[+] Running security analysis...")
    print("--------------------------------------------------")
    print(result["report_md"])
    return 0


async def _run_analyze_file(path_str: str) -> int:
    path = Path(path_str)

    if not path.exists():
        print(f"[!] File not found: {path}")
        return 1

    payload = path.read_text(encoding="utf-8", errors="ignore")
    return await _run_analyze(payload)


async def main() -> int:
    args = sys.argv[1:]

    if not args:
        _print_usage()
        return 1

    command = args[0].lower()

    if command == "analyze":
        if len(args) < 2:
            print("[!] Missing payload.")
            _print_usage()
            return 1

        payload = " ".join(args[1:])
        return await _run_analyze(payload)

    if command == "analyze-file":
        if len(args) < 2:
            print("[!] Missing file path.")
            _print_usage()
            return 1

        return await _run_analyze_file(args[1])

    print(f"[!] Unknown command: {command}")
    _print_usage()
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))