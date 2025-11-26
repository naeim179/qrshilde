import qrcode
from PIL import Image
from pathlib import Path


def decode_from_image(path: str) -> str:
    """
    هنا لاحقاً ممكن تستخدم مكتبة مثل `pyzbar` أو `opencv` لفك ترميز QR.
    حالياً placeholder.
    """
    # TODO: implement real decode
    raise NotImplementedError("QR decoding not implemented yet.")


def generate_qr(data: str, out_path: str) -> None:
    img = qrcode.make(data)
    out_file = Path(out_path)
    img.save(out_file)
