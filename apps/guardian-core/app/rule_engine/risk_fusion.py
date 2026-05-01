from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from guardian_shared.enums import EventType, RiskLevel


RISK_ORDER = {
    RiskLevel.P0: 0,
    RiskLevel.P1: 1,
    RiskLevel.P2: 2,
    RiskLevel.P3: 3,
    RiskLevel.P4: 4,
}


@dataclass(frozen=True)
class RuleResult:
    event_type: EventType | str
    risk_level: RiskLevel
    risk_score: float
    summary: str
    source: str
    room: str | None = None
    trace: dict[str, Any] = field(default_factory=dict)


def more_severe(left: RiskLevel, right: RiskLevel) -> RiskLevel:
    return left if RISK_ORDER[left] <= RISK_ORDER[right] else right


def fuse(results: list[RuleResult]) -> RuleResult:
    if not results:
        return RuleResult(
            event_type=EventType.NORMAL,
            risk_level=RiskLevel.P4,
            risk_score=0.0,
            summary="未检测到异常。",
            source="fusion",
        )
    highest = min(results, key=lambda item: RISK_ORDER[item.risk_level])
    if len([item for item in results if item.risk_level != RiskLevel.P4]) >= 2 and highest.risk_level == RiskLevel.P2:
        return RuleResult(
            event_type=highest.event_type,
            risk_level=RiskLevel.P1,
            risk_score=max(highest.risk_score, 0.75),
            summary=f"多源异常叠加：{highest.summary}",
            source="fusion",
            room=highest.room,
            trace={"fused": [item.trace for item in results]},
        )
    return highest

