import cv2
import numpy as np
import os
from qrshilde.qr_decode import decode_qr_image


def multiple_decode(image_path: str, tries: int = 5) -> int:
    """
    ✅ يجرب فك التشفير بـ thresholds مختلفة عشان يكتشف تناقضات.
    لو القيم اختلفت = QR مشبوه.
    """
    img = cv2.imread(image_path)
    if img is None:
        return 1

    results = []
    thresholds = [60, 90, 120, 150, 180]

    for t in thresholds[:tries]:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, processed = cv2.threshold(gray, t, 255, cv2.THRESH_BINARY)
        temp_path = f"/tmp/qr_temp_{t}.png"
        cv2.imwrite(temp_path, processed)

        try:
            decoded = decode_qr_image(temp_path)
            values = tuple(
                obj.data.decode("utf-8", errors="ignore")
                for obj in decoded
            )
            results.append(values)
        except Exception:
            results.append(())
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    return len(set(results))


def noise(image_path: str) -> float:
    """قياس مستوى الضوضاء في الصورة."""
    img = cv2.imread(image_path)
    if img is None:
        return 0.0

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)

    return float(np.sum(edges) / edges.size)


def symmetry(image_path: str) -> float:
    """
    ✅ QR codes الحقيقية غير متماثلة (قيمة عالية = طبيعي).
    قيمة منخفضة جداً = صورة متماثلة = مشبوهة.
    """
    img = cv2.imread(image_path)
    if img is None:
        return 50.0  # قيمة محايدة

    flip = cv2.flip(img, 1)
    diff = np.mean(cv2.absdiff(img, flip))

    return float(diff)


def detect_fake_qr(image_path: str) -> dict:
    score = 0
    details_log = []

    c = multiple_decode(image_path)
    n = noise(image_path)
    s = symmetry(image_path)

    # ✅ تناقض في فك التشفير = مشبوه
    if c > 1:
        score += 40
        details_log.append("Inconsistent decoding across thresholds")

    # ✅ ضوضاء عالية جداً = مشبوهة (threshold مرفوع لتقليل false positives)
    if n > 0.35:
        score += 30
        details_log.append("High noise level detected")

    # ✅ تماثل عالي = QR مزيف (QR الحقيقي غير متماثل)
    if s < 10:
        score += 30
        details_log.append("Suspicious symmetry (too uniform for a real QR)")

    final_score = min(100, score)

    return {
        "fake_qr_score": final_score,
        "risk_level": "HIGH" if final_score >= 60 else "MEDIUM" if final_score >= 30 else "LOW",
        "details": {
            "consistency": c,
            "noise": round(n, 3),
            "symmetry": round(s, 2),
        },
        "flags": details_log,
    }