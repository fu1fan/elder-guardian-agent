from __future__ import annotations

from guardian_shared.enums import RiskLevel


def should_notify_family_on_timeout(risk_level: str) -> bool:
    return RiskLevel(risk_level) in {RiskLevel.P1, RiskLevel.P2}


def timeout_escalation_level(risk_level: str) -> RiskLevel:
    if RiskLevel(risk_level) == RiskLevel.P2:
        return RiskLevel.P1
    return RiskLevel(risk_level)

