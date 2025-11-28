def build_report_markdown(qr_text, meta, risk_score, ai_section, ai_error, generated_at):
    lines = []
    lines.append("# QR Security Analysis Report\n")
    lines.append(f"- Generated at: `{generated_at}`")
    lines.append(f"- Risk Score: **{risk_score}/100**\n")

    lines.append("## QR Content\n")
    lines.append("```text")
    lines.append(qr_text)
    lines.append("```\n")

    lines.append("## Detected Metadata\n")
    for k, v in meta.items():
        lines.append(f"- **{k}**: `{v}`")
    lines.append("")

    lines.append("## AI Analysis\n")
    if ai_section:
        lines.append(ai_section)
    else:
        if ai_error and "insufficient_quota" in ai_error:
            lines.append(
                "> [AI disabled] OpenAI quota exceeded on this API key. "
                "Report generated using local heuristics only."
            )
        elif ai_error:
            lines.append(f"> [AI error] {ai_error}")
        else:
            lines.append(
                "> [AI disabled] No AI analysis was performed."
            )

    lines.append("\n## Risk Interpretation\n")
    if risk_score >= 80:
        lines.append("- **Critical Risk**: Avoid scanning/using this QR at all.")
    elif risk_score >= 50:
        lines.append("- **Medium Risk**: Treat with caution and verify source.")
    else:
        lines.append("- **Low Risk**: No obvious red flags found, but always stay cautious.")

    return "\n".join(lines)
