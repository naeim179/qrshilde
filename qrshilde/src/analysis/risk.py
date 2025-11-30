# qrshilde/src/analysis/risk.py

from __future__ import annotations
from typing import List, Dict, Any


def score_from_attacks(attacks: List[Dict[str, Any]]) -> int:
    """
    Convert detected attacks into a numeric risk score (0–100).
    Simple heuristic: نجمع الأوزان ونقصهم لو زادوا كثير.
    """
    if not attacks:
        return 10  # قليل جداً بس مش صفر

    weights = {
        "login_page_url": 25,
        "suspicious_domain_pattern": 20,
        "qrljacking_candidate": 35,
    }

    score = 0
    for attack in attacks:
        attack_id = attack.get("id")
        score += weights.get(attack_id, 10)

    # نحط حدود منطقية
    score = max(0, min(score, 95))
    return score


def risk_level(score: int) -> str:
    """
    Translate numeric score into human-readable bucket.
    """
    if score >= 80:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"
