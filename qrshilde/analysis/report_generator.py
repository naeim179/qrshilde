def build_markdown_report(analysis: dict) -> str:
    payload = analysis.get("payload", "")
    payload_type = analysis.get("payload_type", "unknown")
    verdict = analysis.get("verdict", "LOW")
    risk_score = analysis.get("risk_score", analysis.get("final_score", 0))
    rule_score = analysis.get("rule_score", 0)
    ml_score = analysis.get("ml_score", 0)
    confidence = analysis.get("confidence")
    recommendation = analysis.get("recommendation")
    generated_at = analysis.get("generated_at", "unknown")

    findings = analysis.get("findings", []) or []
    benign = analysis.get("benign", []) or []
    score_breakdown = analysis.get("score_breakdown", []) or []
    url_analysis = analysis.get("url_analysis")

    lines: list[str] = []
    lines.append("# QR Security Analysis Report")
    lines.append("")
    lines.append(f"- Generated at: {generated_at}")
    lines.append(f"- Payload Type: **{payload_type}**")
    lines.append(f"- Verdict: **{verdict}**")
    lines.append(f"- Risk Score: **{risk_score}/100**")
    lines.append(f"- Rule Score: **{rule_score}/100**")
    lines.append(f"- ML Score: **{ml_score}/100**")
    if confidence is not None:
        lines.append(f"- Confidence: **{confidence}**")
    if recommendation:
        lines.append(f"- Recommendation: {recommendation}")
    lines.append("")

    lines.append("## QR Content")
    lines.append("")
    lines.append("```text")
    lines.append(payload)
    lines.append("```")
    lines.append("")

    lines.append("## Findings")
    if findings:
        for item in findings:
            lines.append(f"- {item}")
    else:
        lines.append("- No findings.")
    lines.append("")

    lines.append("## Benign Signals")
    if benign:
        for item in benign:
            lines.append(f"- {item}")
    else:
        lines.append("- None.")
    lines.append("")

    if score_breakdown:
        lines.append("## Score Breakdown")
        for item in score_breakdown:
            source = item.get("source", "rule")
            points = item.get("points", 0)
            reason = item.get("reason", "")
            lines.append(f"- **{source}**: +{points} — {reason}")
        lines.append("")

    if url_analysis:
        lines.append("## URL Analysis")
        lines.append("")
        lines.append(f"- URL: `{url_analysis.get('url', '')}`")
        lines.append(f"- Domain: `{url_analysis.get('domain', '')}`")
        lines.append(f"- Scheme: `{url_analysis.get('scheme', '')}`")
        lines.append(f"- URL Rule Score: **{url_analysis.get('rule_score', 0)}/100**")
        lines.append(f"- URL ML Score: **{url_analysis.get('ml_score', 0)}/100**")
        lines.append(f"- URL Final Score: **{url_analysis.get('risk_score', 0)}/100**")
        lines.append("")

        url_findings = url_analysis.get("findings", []) or []
        url_benign = url_analysis.get("benign", []) or []
        url_score_breakdown = url_analysis.get("score_breakdown", []) or []
        ml = url_analysis.get("ml")

        lines.append("### URL Findings")
        if url_findings:
            for item in url_findings:
                lines.append(f"- {item}")
        else:
            lines.append("- None.")
        lines.append("")

        lines.append("### URL Benign Signals")
        if url_benign:
            for item in url_benign:
                lines.append(f"- {item}")
        else:
            lines.append("- None.")
        lines.append("")

        if url_score_breakdown:
            lines.append("### URL Score Breakdown")
            for item in url_score_breakdown:
                points = item.get("points", 0)
                reason = item.get("reason", "")
                lines.append(f"- +{points} — {reason}")
            lines.append("")

        if ml:
            lines.append("### ML Output")
            lines.append(f"- Label: **{ml.get('label', '')}**")
            lines.append(f"- Phishing Probability: `{ml.get('phishing_probability')}`")
            lines.append(f"- Threshold: `{ml.get('threshold')}`")
            reasons = ml.get("reasons", []) or []
            if reasons:
                lines.append("- Top Reasons:")
                for reason in reasons:
                    feature = reason.get("feature", "")
                    impact = reason.get("impact", "")
                    lines.append(f"  - {feature}: {impact}")
            lines.append("")

    return "\n".join(lines)