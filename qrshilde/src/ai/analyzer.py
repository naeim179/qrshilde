from .openai_client import ask_model
from .prompts import build_qr_analysis_prompt
from src.analysis.classifier import extract_basic_meta
from src.analysis.risk_score import basic_risk_score


def analyze_qr_payload(payload: str) -> dict:
    """
    دالة مركزية:
    - تحلل الـ payload محلياً (type + meta + risk score)
    - تطلب من الـ AI تحليل كامل
    - ترجّع dict جاهزة تستخدمها الـ CLI أو واجهة ويب
    """
    meta = extract_basic_meta(payload)
    risk = basic_risk_score(meta)
    prompt = build_qr_analysis_prompt(payload, meta)

    ai_text = ask_model(prompt)

    return {
      "payload": payload,
      "meta": meta,
      "risk_score": risk,
      "ai_report": ai_text,
    }
