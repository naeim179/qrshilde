import asyncio
import sys

from qrshilde.qr_analyze import main


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))