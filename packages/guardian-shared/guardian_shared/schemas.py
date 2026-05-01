from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from .enums import DeviceAction, DeviceType, EventState, EventType, RiskLevel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class GuardianModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="ignore")


class SensorVitalSample(GuardianModel):
    sample_id: str = Field(default_factory=lambda: new_id("vital"))
    elder_id: str
    heart_rate: int
    spo2: int
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    body_temperature: float | None = None
    timestamp: datetime = Field(default_factory=utc_now)


class SensorEnvSample(GuardianModel):
    sample_id: str = Field(default_factory=lambda: new_id("env"))
    elder_id: str
    room: str = "living_room"
    temperature: float
    humidity: float
    co2_ppm: int
    gas_ppm: int = 0
    smoke_ppm: int = 0
    timestamp: datetime = Field(default_factory=utc_now)


class VisionEvent(GuardianModel):
    event_id: str = Field(default_factory=lambda: new_id("vision"))
    elder_id: str
    room: str = "living_room"
    event_type: EventType
    confidence: float = 0.0
    posture: str = "unknown"
    motion_state: str = "unknown"
    snapshot_path: str | None = None
    timestamp: datetime = Field(default_factory=utc_now)


class HomeDeviceState(GuardianModel):
    state_id: str = Field(default_factory=lambda: new_id("state"))
    elder_id: str | None = None
    room: str
    device: DeviceType | str
    state: str
    value: Any = None
    online: bool = True
    timestamp: datetime = Field(default_factory=utc_now)


class HomeDeviceCommand(GuardianModel):
    cmd_id: str = Field(default_factory=lambda: new_id("cmd"))
    elder_id: str
    room: str
    device: DeviceType | str
    action: DeviceAction | str
    value: Any = None
    reason: str
    priority: RiskLevel = RiskLevel.P3
    require_ack: bool = True
    ttl_sec: int = 30
    timestamp: datetime = Field(default_factory=utc_now)


class RiskEvent(GuardianModel):
    event_id: str = Field(default_factory=lambda: new_id("risk"))
    elder_id: str
    event_type: EventType | str
    risk_level: RiskLevel
    risk_score: float = 0.0
    state: EventState = EventState.EVENT_DETECTED
    source: str
    room: str | None = None
    summary: str = ""
    rule_trace: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AgentDecision(GuardianModel):
    risk_level: RiskLevel
    risk_score: float = 0.0
    event_type: str
    reasoning_summary: str
    recommended_actions: list[str] = Field(default_factory=list)
    need_elder_confirmation: bool = True
    need_family_notification: bool = False
    alert_priority: RiskLevel
    device_actions: list[dict[str, Any]] = Field(default_factory=list)


class HmiPrompt(GuardianModel):
    prompt_id: str = Field(default_factory=lambda: new_id("prompt"))
    event_id: str
    elder_id: str
    risk_level: RiskLevel
    event_type: str
    message: str
    options: list[str] = Field(default_factory=lambda: ["我没事", "需要帮助", "联系家属"])
    timeout_sec: int = 30
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None

    def with_expiry(self) -> "HmiPrompt":
        data = self.model_dump()
        data["expires_at"] = self.created_at + timedelta(seconds=self.timeout_sec)
        return HmiPrompt(**data)


class HmiResponse(GuardianModel):
    response_id: str = Field(default_factory=lambda: new_id("response"))
    prompt_id: str
    event_id: str
    elder_id: str
    response_type: str
    response_text: str
    timestamp: datetime = Field(default_factory=utc_now)


class AlertRecord(GuardianModel):
    alert_id: str = Field(default_factory=lambda: new_id("alert"))
    event_id: str
    elder_id: str
    priority: RiskLevel
    channel: str = "mock_wechat"
    message: str
    status: str = "sent"
    timestamp: datetime = Field(default_factory=utc_now)


class AgentRunRecord(GuardianModel):
    run_id: str = Field(default_factory=lambda: new_id("run"))
    event_id: str
    elder_id: str
    context: dict[str, Any] = Field(default_factory=dict)
    decision: AgentDecision
    llm_mock: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class DashboardMessage(GuardianModel):
    type: str
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)

