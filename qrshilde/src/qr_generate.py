import argparse
import qrcode
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Generate a QR Code.")

    # استقبال النص مباشرة بدون --text
    parser.add_argument(
        "text", 
        type=str, 
        help="The text or URL to encode in the QR code"
    )

    parser.add_argument(
        "-o", "--out", 
        type=str, 
        default="qrcode.png", 
        help="Output image file path (default: qrcode.png)"
    )

    args = parser.parse_args()

    # ✅ التعديل الجوهري: version=None يجعل المكتبة تختار الحجم المناسب تلقائياً
    # هذا يمنع تلف الباركود عند وضع رابط طويل
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(args.text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    out_path = Path(args.out)
    img.save(out_path)
    print(f"[+] QR code generated and saved to: {out_path}")

if __name__ == "__main__":
    main()