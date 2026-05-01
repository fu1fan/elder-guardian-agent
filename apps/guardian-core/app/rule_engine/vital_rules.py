from __future__ import annotations

from guardian_shared.enums import EventType, RiskLevel
from guardian_shared.schemas import SensorVitalSample

from app.rule_engine.risk_fusion import RuleResult


def classify_vital(sample: SensorVitalSample) -> RuleResult:
    trace = {
        "heart_rate": sample.heart_rate,
        "spo2": sample.spo2,
        "body_temperature": sample.body_temperature,
    }
    if sample.spo2 < 88:
        return RuleResult(
            event_type=EventType.SPO2_LOW,
            risk_level=RiskLevel.P0,
            risk_score=0.98,
            summary=f"血氧 {sample.spo2}% 低于 88%，属于紧急风险。",
            source="vital",
            trace=trace,
        )
    if sample.spo2 < 92:
        return RuleResult(
            event_type=EventType.SPO2_LOW,
            risk_level=RiskLevel.P1,
            risk_score=0.85,
            summary=f"血氧 {sample.spo2}% 明显偏低，需要同步通知家属并本地确认。",
            source="vital",
            trace=trace,
        )
    if sample.heart_rate < 45 or sample.heart_rate > 130:
        return RuleResult(
            event_type=EventType.HEART_RATE_ABNORMAL,
            risk_level=RiskLevel.P1,
            risk_score=0.82,
            summary=f"心率 {sample.heart_rate} 次/分异常明显。",
            source="vital",
            trace=trace,
        )
    if sample.heart_rate < 55 or sample.heart_rate > 110:
        return RuleResult(
            event_type=EventType.HEART_RATE_ABNORMAL,
            risk_level=RiskLevel.P2,
            risk_score=0.58,
            summary=f"心率 {sample.heart_rate} 次/分轻度异常，先询问老人状态。",
            source="vital",
            trace=trace,
        )
    return RuleResult(
        event_type=EventType.NORMAL,
        risk_level=RiskLevel.P4,
        risk_score=0.05,
        summary="生命体征处于 MVP 正常范围。",
        source="vital",
        trace=trace,
    )

