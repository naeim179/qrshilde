# qrshilde/src/ai/analyzer.py

from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from qrshilde.src.analysis.classifier import extract_basic_meta, detect_attacks
from qrshilde.src.analysis.risk import score_from_attacks, risk_level
from qrshilde.src.analysis.report import build_report_markdown
from qrshilde.src.ai.openai_client import ask_model_safe  # شوف الملاحظة تحت
from qrshilde.src.ai.prompts import build_qr_analysis_prompt


def analyze_qr_payload(qr_text: str) -> Dict[str, Any]:
    """
    Main entry point for QR analysis.
    Returns a dict suitable for:
      - CLI Markdown report
      - future JSON API / frontend
    """
    generated_at = datetime.now(timezone.utc).isoformat()

    # 1) Basic metadata
    meta = extract_basic_meta(qr_text)

    # 2) Rule-based attack detection
    attacks = detect_attacks(qr_text, meta)
    risk_score = score_from_attacks(attacks)
    level = risk_level(risk_score)

    # 3) Optional AI analysis
    ai_text: Optional[str] = None
    ai_error: Optional[str] = None
    ai_raw: Optional[Any] = None

    try:
        prompt = build_qr_analysis_prompt(qr_text, meta, attacks, risk_score, level)
        ok, result = ask_model_safe(prompt)
        if ok:
            ai_raw = result
            # لو result عندك أصلاً Markdown خليه زي ما هو
            ai_text = result.get("markdown") or result.get("text") or str(result)
        else:
            ai_error = result  # رسالة خطأ من ask_model_safe
    except Exception as e:
        ai_error = f"AI error: {e}"

    # 4) Build Markdown report
    report_md = build_report_markdown(
        qr_text=qr_text,
        meta=meta,
        risk_score=risk_score,
        risk_level=level,
        attacks=attacks,
        ai_section=ai_text,
        ai_error=ai_error,
        generated_at=generated_at,
    )

    # 5) JSON-style structured output
    return {
        "qr_text": qr_text,
        "generated_at": generated_at,
        "meta": meta,
        "attacks": attacks,
        "risk_score": risk_score,
        "risk_level": level,
        "ai": {
            "enabled": ai_text is not None,
            "error": ai_error,
            "raw": ai_raw,
            "summary": ai_text,
        },
        "report_md": report_md,
    }
