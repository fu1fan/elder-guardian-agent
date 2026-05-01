from __future__ import annotations

from guardian_shared.enums import EventType, RiskLevel
from guardian_shared.schemas import SensorEnvSample

from app.rule_engine.risk_fusion import RuleResult


def classify_env(sample: SensorEnvSample) -> RuleResult:
    trace = {
        "room": sample.room,
        "temperature": sample.temperature,
        "humidity": sample.humidity,
        "co2_ppm": sample.co2_ppm,
        "gas_ppm": sample.gas_ppm,
        "smoke_ppm": sample.smoke_ppm,
    }
    if sample.gas_ppm >= 100:
        return RuleResult(
            event_type=EventType.GAS_LEAK,
            risk_level=RiskLevel.P0,
            risk_score=1.0,
            summary=f"{sample.room} 燃气浓度 {sample.gas_ppm} ppm，直接进入 P0 告警。",
            source="environment",
            room=sample.room,
            trace=trace,
        )
    if sample.smoke_ppm >= 80:
        return RuleResult(
            event_type=EventType.GAS_LEAK,
            risk_level=RiskLevel.P0,
            risk_score=1.0,
            summary=f"{sample.room} 烟雾浓度 {sample.smoke_ppm} ppm，直接进入 P0 告警。",
            source="environment",
            room=sample.room,
            trace=trace,
        )
    if sample.co2_ppm >= 1500:
        return RuleResult(
            event_type=EventType.CO2_HIGH,
            risk_level=RiskLevel.P3,
            risk_score=0.42,
            summary=f"{sample.room} CO2 {sample.co2_ppm} ppm 偏高，建议自动通风。",
            source="environment",
            room=sample.room,
            trace=trace,
        )
    if sample.temperature >= 30:
        return RuleResult(
            event_type=EventType.TEMPERATURE_HIGH,
            risk_level=RiskLevel.P3,
            risk_score=0.38,
            summary=f"{sample.room} 温度 {sample.temperature:.1f} 摄氏度偏高，建议降温。",
            source="environment",
            room=sample.room,
            trace=trace,
        )
    if sample.temperature <= 16:
        return RuleResult(
            event_type=EventType.TEMPERATURE_LOW,
            risk_level=RiskLevel.P3,
            risk_score=0.38,
            summary=f"{sample.room} 温度 {sample.temperature:.1f} 摄氏度偏低，建议升温。",
            source="environment",
            room=sample.room,
            trace=trace,
        )
    return RuleResult(
        event_type=EventType.NORMAL,
        risk_level=RiskLevel.P4,
        risk_score=0.03,
        summary="居家环境处于 MVP 正常范围。",
        source="environment",
        room=sample.room,
        trace=trace,
    )

