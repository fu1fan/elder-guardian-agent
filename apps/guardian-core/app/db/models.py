from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SensorVitalSampleModel(Base):
    __tablename__ = "sensor_vital_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    elder_id: Mapped[str] = mapped_column(String(64), index=True)
    heart_rate: Mapped[int] = mapped_column(Integer)
    spo2: Mapped[int] = mapped_column(Integer)
    systolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diastolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    raw_json: Mapped[str] = mapped_column(Text, default="{}")


class SensorEnvSampleModel(Base):
    __tablename__ = "sensor_env_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    elder_id: Mapped[str] = mapped_column(String(64), index=True)
    room: Mapped[str] = mapped_column(String(64), index=True)
    temperature: Mapped[float] = mapped_column(Float)
    humidity: Mapped[float] = mapped_column(Float)
    co2_ppm: Mapped[int] = mapped_column(Integer)
    gas_ppm: Mapped[int] = mapped_column(Integer, default=0)
    smoke_ppm: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    raw_json: Mapped[str] = mapped_column(Text, default="{}")


class VisionEventModel(Base):
    __tablename__ = "vision_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    elder_id: Mapped[str] = mapped_column(String(64), index=True)
    room: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    posture: Mapped[str] = mapped_column(String(64), default="unknown")
    motion_state: Mapped[str] = mapped_column(String(64), default="unknown")
    snapshot_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    raw_json: Mapped[str] = mapped_column(Text, default="{}")


class HomeDeviceStateModel(Base):
    __tablename__ = "home_device_states"
    __table_args__ = (UniqueConstraint("room", "device", name="uq_home_device"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    state_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    elder_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    room: Mapped[str] = mapped_column(String(64), index=True)
    device: Mapped[str] = mapped_column(String(64), index=True)
    state: Mapped[str] = mapped_column(String(64))
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    online: Mapped[bool] = mapped_column(Boolean, default=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    raw_json: Mapped[str] = mapped_column(Text, default="{}")


class RiskEventModel(Base):
    __tablename__ = "risk_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    elder_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    risk_level: Mapped[str] = mapped_column(String(8), index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    state: Mapped[str] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    room: Mapped[str | None] = mapped_column(String(64), nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    rule_trace_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentRunModel(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    event_id: Mapped[str] = mapped_column(String(64), index=True)
    elder_id: Mapped[str] = mapped_column(String(64), index=True)
    context_json: Mapped[str] = mapped_column(Text, default="{}")
    decision_json: Mapped[str] = mapped_column(Text, default="{}")
    llm_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class AlertRecordModel(Base):
    __tablename__ = "alert_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    alert_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    event_id: Mapped[str] = mapped_column(String(64), index=True)
    elder_id: Mapped[str] = mapped_column(String(64), index=True)
    priority: Mapped[str] = mapped_column(String(8), index=True)
    channel: Mapped[str] = mapped_column(String(64), default="mock_wechat")
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default="sent")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class HmiPromptModel(Base):
    __tablename__ = "hmi_prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prompt_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    event_id: Mapped[str] = mapped_column(String(64), index=True)
    elder_id: Mapped[str] = mapped_column(String(64), index=True)
    risk_level: Mapped[str] = mapped_column(String(8), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(Text)
    options_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(64), default="waiting", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class HmiResponseModel(Base):
    __tablename__ = "hmi_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    response_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    prompt_id: Mapped[str] = mapped_column(String(64), index=True)
    event_id: Mapped[str] = mapped_column(String(64), index=True)
    elder_id: Mapped[str] = mapped_column(String(64), index=True)
    response_type: Mapped[str] = mapped_column(String(64), index=True)
    response_text: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class DeviceCommandModel(Base):
    __tablename__ = "device_commands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cmd_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    event_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    elder_id: Mapped[str] = mapped_column(String(64), index=True)
    room: Mapped[str] = mapped_column(String(64), index=True)
    device: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(64))
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(8), index=True)
    require_ack: Mapped[bool] = mapped_column(Boolean, default=True)
    ttl_sec: Mapped[int] = mapped_column(Integer, default=30)
    status: Mapped[str] = mapped_column(String(64), default="sent", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    ack_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_json: Mapped[str] = mapped_column(Text, default="{}")

