from dataclasses import dataclass, field
from typing import Any, Literal

RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
Action = Literal["ALLOW", "SANDBOX_PREVIEW", "BLOCK"]

@dataclass
class InspectionResult:
    content_type: str
    payload: str
    details: dict[str, Any] = field(default_factory=dict)

@dataclass
class AnalysisResult:
    content_type: str
    payload: str
    risk_level: RiskLevel
    risk_score: int
    recommended_action: Action
    reasons: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
