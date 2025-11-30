# qrshilde/src/analysis/report.py

from __future__ import annotations
from typing import Dict, Any, List, Optional


def build_report_markdown(
    qr_text: str,
    meta: Dict[str, Any],
    risk_score: int,
    risk_level: str,
    attacks: List[Dict[str, Any]],
    ai_section: Optional[str],
    ai_error: Optional[str],
    generated_at: str,
) -> str:
    """
    Build a human-readable Markdown report for CLI / files.
    """
    lines: List[str] = []

    lines.append("# QR Security Analysis Report\n")
    lines.append(f"- Generated at: `{generated_at}`")
    lines.append(f"- Risk Score: **{risk_score}/100**")
    lines.append(f"- Risk Level: **{risk_level}**\n")

    # QR content
    lines.append("## QR Content\n")
    lines.append("```text")
    lines.append(qr_text)
    lines.append("```\n")

    # Metadata
    lines.append("## Detected Metadata\n")
    if meta:
        for k in ["qr_type", "scheme", "domain", "path"]:
            if meta.get(k) is not None:
                lines.append(f"- **{k}**: `{meta[k]}`")
    if meta.get("is_url") and meta.get("query"):
        lines.append("- **query params**: present")
    lines.append("")

    # Detected attacks
    lines.append("## Detected Issues (Rule-based)\n")
    if attacks:
        for atk in attacks:
            lines.append(f"- **{atk.get('title', atk.get('id'))}** "
                         f"(_{atk.get('severity', 'unknown')}_): {atk.get('reason', '')}")
    else:
        lines.append("- No specific attack patterns detected by rule engine.")
    lines.append("")

    # AI section
    lines.append("## AI Analysis\n")
    if ai_section:
        lines.append(ai_section.strip())
        lines.append("")
    elif ai_error:
        lines.append(f"[AI disabled / error] {ai_error}")
        lines.append("")
    else:
        lines.append("[AI not configured] No advanced analysis available.\n")

    # Risk interpretation
    lines.append("## Risk Interpretation\n")
    if risk_level in ("Critical", "High"):
        lines.append("- **High Risk**: Avoid scanning this QR with a production device.")
        lines.append("- Do not enter credentials or sensitive data on pages opened via this QR.")
    elif risk_level == "Medium":
        lines.append("- **Medium Risk**: Some suspicious indicators were found. Proceed with caution.")
    else:
        lines.append("- **Low Risk**: No strong red flags, but always stay cautious with unknown QRs.")

    return "\n".join(lines)
