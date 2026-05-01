from __future__ import annotations

from guardian_shared.enums import EventType, RiskLevel
from guardian_shared.schemas import VisionEvent

from app.rule_engine.risk_fusion import RuleResult


def classify_vision(event: VisionEvent) -> RuleResult:
    trace = {
        "room": event.room,
        "event_type": str(event.event_type),
        "confidence": event.confidence,
        "posture": event.posture,
        "motion_state": event.motion_state,
        "snapshot_path": event.snapshot_path,
    }
    if event.event_type == EventType.SUSPECTED_FALL:
        return RuleResult(
            event_type=EventType.SUSPECTED_FALL,
            risk_level=RiskLevel.P1,
            risk_score=max(0.78, event.confidence),
            summary=f"{event.room} 发现疑似跌倒，置信度 {event.confidence:.2f}。",
            source="vision",
            room=event.room,
            trace=trace,
        )
    if event.event_type == EventType.LONG_STATIC:
        return RuleResult(
            event_type=EventType.LONG_STATIC,
            risk_level=RiskLevel.P2,
            risk_score=max(0.62, event.confidence),
            summary=f"{event.room} 长时间静止，先本地询问老人。",
            source="vision",
            room=event.room,
            trace=trace,
        )
    if event.event_type == EventType.NIGHT_ABNORMAL_ACTIVITY:
        return RuleResult(
            event_type=EventType.NIGHT_ABNORMAL_ACTIVITY,
            risk_level=RiskLevel.P1,
            risk_score=max(0.74, event.confidence),
            summary=f"{event.room} 夜间异常活动，需要本地确认并同步家属。",
            source="vision",
            room=event.room,
            trace=trace,
        )
    return RuleResult(
        event_type=EventType.NORMAL,
        risk_level=RiskLevel.P4,
        risk_score=0.02,
        summary="视觉服务未发现异常。",
        source="vision",
        room=event.room,
        trace=trace,
    )

