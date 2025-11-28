from datetime import datetime, timezone

from qrshilde.src.analysis.classifier import extract_basic_meta
from qrshilde.src.analysis.risk import score_risk
from qrshilde.src.analysis.report import build_report_markdown
# لاحظ: ما عاد نستخدم ask_model ولا prompts هنا


def analyze_qr_payload(qr_text: str) -> dict:
    """
    Analyze QR text using local heuristics only (no external AI).
    """

    meta = extract_basic_meta(qr_text)
    risk_score = score_risk(qr_text)
    generated_at = datetime.now(timezone.utc).isoformat()

    # ما في AI هنا
    ai_section = None
    ai_error = "AI backend disabled (no API quota / external model)."

    report_md = build_report_markdown(
        qr_text=qr_text,
        meta=meta,
        risk_score=risk_score,
        ai_section=ai_section,
        ai_error=ai_error,
        generated_at=generated_at,
    )

    return {
        "qr_text": qr_text,
        "meta": meta,
        "risk_score": risk_score,
        "ai_section": ai_section,
        "ai_error": ai_error,
        "generated_at": generated_at,
        "report_md": report_md,
    }
