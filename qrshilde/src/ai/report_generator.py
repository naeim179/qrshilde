from datetime import datetime
from textwrap import indent


def build_markdown_report(analysis: dict) -> str:
    """
    يبني تقرير Markdown مبني على نتيجة analyze_qr_payload
    """
    payload = analysis.get("payload", "")
    meta = analysis.get("meta", {})
    risk = analysis.get("risk_score", 0)
    ai_report = analysis.get("ai_report", "")

    lines = []
    lines.append("# QR Security Analysis Report")
    lines.append("")
    lines.append(f"- Generated at: {datetime.utcnow().isoformat()} UTC")
    lines.append(f"- Risk Score: **{risk}/100**")
    lines.append("")
    lines.append("## QR Content")
    lines.append("")
    lines.append("```text")
    lines.append(payload)
    lines.append("```")
    lines.append("")

    if meta:
        lines.append("## Detected Metadata")
        lines.append("")
        for k, v in meta.items():
            lines.append(f"- **{k}**: `{v}`")
        lines.append("")

    if ai_report:
        lines.append("## AI Analysis")
        lines.append("")
        # نخلي النتيجة مرتبة
        lines.append(indent(ai_report, ""))
        lines.append("")

    return "\n".join(lines)
