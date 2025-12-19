from qrshilde.src.engine.types import InspectionResult, AnalysisResult
from qrshilde.src.engine.router import should_use_groq
from qrshilde.src.engine.decision import groq_decide
from qrshilde.src.qr_inspect import classify_payload


def inspect(payload: str) -> InspectionResult:
    r = classify_payload(payload)
    return InspectionResult(
        content_type=r.get("type", "unknown"),
        payload=r.get("text", payload),
        details=r.get("details", {})
    )


def collect_tool_signals(ins: InspectionResult) -> dict:
    signals = {
        "patterns": [],
        "url_scan": None,
        "wifi_risk": None
    }

    try:
        from qrshilde.tools.malicious_pattern_detector import detect_malicious_patterns
        signals["patterns"] = detect_malicious_patterns(ins.payload) or []
    except Exception:
        pass

    if ins.content_type == "url":
        try:
            from qrshilde.tools.url_scanner import scan_url
            signals["url_scan"] = scan_url(ins.payload)
        except Exception:
            pass

    if ins.content_type == "wifi":
        try:
            from qrshilde.tools.wifi_auto_connect_detector import detect_wifi_risk
            signals["wifi_risk"] = detect_wifi_risk(ins.payload)
        except Exception:
            pass

    return signals


def analyze_payload(payload: str) -> AnalysisResult:
    ins = inspect(payload)
    signals = collect_tool_signals(ins)

    decision = {
        "risk_score": 15,
        "risk_level": "LOW",
        "recommended_action": "ALLOW",
        "reasons": []
    }

    if ins.content_type in {"url", "wifi", "sms"}:
        decision["risk_score"] = max(decision["risk_score"], 55)
        decision["risk_level"] = "MEDIUM"
        decision["recommended_action"] = "SANDBOX_PREVIEW"
        decision["reasons"].append(f"Sensitive QR type: {ins.content_type}")

    if signals.get("patterns"):
        decision["risk_score"] = max(decision["risk_score"], 70)
        decision["risk_level"] = "HIGH"
        decision["recommended_action"] = "SANDBOX_PREVIEW"
        decision["reasons"].append("Malicious patterns detected")

    if should_use_groq(ins.content_type, ins.payload):
        try:
            ai = groq_decide(
                ins.payload,
                {"type": ins.content_type, "details": ins.details},
                signals
            )
            decision = ai
        except Exception:
            decision["reasons"].append(
                "Groq unavailable; used rule-based classification."
            )

    return AnalysisResult(
        content_type=ins.content_type,
        payload=ins.payload,
        risk_level=decision["risk_level"],
        risk_score=int(decision["risk_score"]),
        recommended_action=decision["recommended_action"],
        reasons=decision.get("reasons", []),
        details={
            "inspection": ins.details,
            "signals": signals
        }
    )
