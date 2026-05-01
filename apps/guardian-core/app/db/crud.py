from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from guardian_shared.enums import EventState
from guardian_shared.schemas import (
    AgentDecision,
    AgentRunRecord,
    AlertRecord,
    HmiPrompt,
    HmiResponse,
    HomeDeviceCommand,
    HomeDeviceState,
    RiskEvent,
    SensorEnvSample,
    SensorVitalSample,
    VisionEvent,
)

from app.db import models


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json(value: Any) -> str:
    if hasattr(value, "model_dump"):
        return json.dumps(value.model_dump(mode="json"), ensure_ascii=False, default=str)
    return json.dumps(value, ensure_ascii=False, default=str)


def _loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def row_to_dict(row: Any) -> dict[str, Any]:
    data = {column.name: getattr(row, column.name) for column in row.__table__.columns}
    for key, value in list(data.items()):
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    for key in ["raw_json", "rule_trace_json", "context_json", "decision_json", "options_json"]:
        if key in data:
            data[key.replace("_json", "")] = _loads(data.pop(key), {} if key != "options_json" else [])
    return data


def create_vital_sample(db: Session, sample: SensorVitalSample) -> models.SensorVitalSampleModel:
    obj = models.SensorVitalSampleModel(
        sample_id=sample.sample_id,
        elder_id=sample.elder_id,
        heart_rate=sample.heart_rate,
        spo2=sample.spo2,
        systolic_bp=sample.systolic_bp,
        diastolic_bp=sample.diastolic_bp,
        body_temperature=sample.body_temperature,
        timestamp=sample.timestamp,
        raw_json=_json(sample),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_env_sample(db: Session, sample: SensorEnvSample) -> models.SensorEnvSampleModel:
    obj = models.SensorEnvSampleModel(
        sample_id=sample.sample_id,
        elder_id=sample.elder_id,
        room=sample.room,
        temperature=sample.temperature,
        humidity=sample.humidity,
        co2_ppm=sample.co2_ppm,
        gas_ppm=sample.gas_ppm,
        smoke_ppm=sample.smoke_ppm,
        timestamp=sample.timestamp,
        raw_json=_json(sample),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_vision_event(db: Session, event: VisionEvent) -> models.VisionEventModel:
    obj = models.VisionEventModel(
        event_id=event.event_id,
        elder_id=event.elder_id,
        room=event.room,
        event_type=str(event.event_type),
        confidence=event.confidence,
        posture=event.posture,
        motion_state=event.motion_state,
        snapshot_path=event.snapshot_path,
        timestamp=event.timestamp,
        raw_json=_json(event),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_risk_event(db: Session, event: RiskEvent) -> models.RiskEventModel:
    obj = models.RiskEventModel(
        event_id=event.event_id,
        elder_id=event.elder_id,
        event_type=str(event.event_type),
        risk_level=str(event.risk_level),
        risk_score=event.risk_score,
        state=str(event.state),
        source=event.source,
        room=event.room,
        summary=event.summary,
        rule_trace_json=_json(event.rule_trace),
        created_at=event.created_at,
        updated_at=event.updated_at,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_risk_event(db: Session, event_id: str) -> models.RiskEventModel | None:
    return db.query(models.RiskEventModel).filter(models.RiskEventModel.event_id == event_id).first()


def update_risk_event_state(
    db: Session,
    event_id: str,
    state: EventState | str,
    *,
    risk_level: str | None = None,
    summary: str | None = None,
) -> models.RiskEventModel | None:
    obj = get_risk_event(db, event_id)
    if obj is None:
        return None
    obj.state = str(state)
    obj.updated_at = utc_now()
    if risk_level is not None:
        obj.risk_level = risk_level
    if summary is not None:
        obj.summary = summary
    if str(state) in {EventState.RESOLVED.value, EventState.ESCALATED.value, EventState.FAMILY_ALERT.value}:
        obj.resolved_at = utc_now()
    db.commit()
    db.refresh(obj)
    return obj


def create_agent_run(db: Session, run: AgentRunRecord) -> models.AgentRunModel:
    obj = models.AgentRunModel(
        run_id=run.run_id,
        event_id=run.event_id,
        elder_id=run.elder_id,
        context_json=_json(run.context),
        decision_json=_json(run.decision),
        llm_mock=run.llm_mock,
        created_at=run.created_at,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_alert(db: Session, alert: AlertRecord) -> models.AlertRecordModel:
    obj = models.AlertRecordModel(
        alert_id=alert.alert_id,
        event_id=alert.event_id,
        elder_id=alert.elder_id,
        priority=str(alert.priority),
        channel=alert.channel,
        message=alert.message,
        status=alert.status,
        timestamp=alert.timestamp,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_hmi_prompt(db: Session, prompt: HmiPrompt, status: str = "waiting") -> models.HmiPromptModel:
    prompt = prompt.with_expiry() if prompt.expires_at is None else prompt
    obj = models.HmiPromptModel(
        prompt_id=prompt.prompt_id,
        event_id=prompt.event_id,
        elder_id=prompt.elder_id,
        risk_level=str(prompt.risk_level),
        event_type=prompt.event_type,
        message=prompt.message,
        options_json=_json(prompt.options),
        status=status,
        created_at=prompt.created_at,
        expires_at=prompt.expires_at,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_hmi_prompt(db: Session, prompt_id: str) -> models.HmiPromptModel | None:
    return db.query(models.HmiPromptModel).filter(models.HmiPromptModel.prompt_id == prompt_id).first()


def latest_waiting_prompt_for_event(db: Session, event_id: str) -> models.HmiPromptModel | None:
    return (
        db.query(models.HmiPromptModel)
        .filter(models.HmiPromptModel.event_id == event_id, models.HmiPromptModel.status == "waiting")
        .order_by(desc(models.HmiPromptModel.created_at))
        .first()
    )


def update_hmi_prompt_status(
    db: Session,
    prompt_id: str,
    status: str,
    *,
    responded_at: datetime | None = None,
) -> models.HmiPromptModel | None:
    obj = get_hmi_prompt(db, prompt_id)
    if obj is None:
        return None
    obj.status = status
    if responded_at is not None:
        obj.responded_at = responded_at
    db.commit()
    db.refresh(obj)
    return obj


def create_hmi_response(db: Session, response: HmiResponse) -> models.HmiResponseModel:
    obj = models.HmiResponseModel(
        response_id=response.response_id,
        prompt_id=response.prompt_id,
        event_id=response.event_id,
        elder_id=response.elder_id,
        response_type=response.response_type,
        response_text=response.response_text,
        timestamp=response.timestamp,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_device_command(
    db: Session,
    command: HomeDeviceCommand,
    *,
    event_id: str | None = None,
    status: str = "sent",
) -> models.DeviceCommandModel:
    obj = models.DeviceCommandModel(
        cmd_id=command.cmd_id,
        event_id=event_id,
        elder_id=command.elder_id,
        room=command.room,
        device=str(command.device),
        action=str(command.action),
        value=_json(command.value) if command.value is not None else None,
        reason=command.reason,
        priority=str(command.priority),
        require_ack=command.require_ack,
        ttl_sec=command.ttl_sec,
        status=status,
        created_at=command.timestamp,
        raw_json=_json(command),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def mark_device_command_ack(db: Session, cmd_id: str, status: str = "acked") -> models.DeviceCommandModel | None:
    obj = db.query(models.DeviceCommandModel).filter(models.DeviceCommandModel.cmd_id == cmd_id).first()
    if obj is None:
        return None
    obj.status = status
    obj.ack_at = utc_now()
    db.commit()
    db.refresh(obj)
    return obj


def upsert_device_state(db: Session, state: HomeDeviceState) -> models.HomeDeviceStateModel:
    obj = (
        db.query(models.HomeDeviceStateModel)
        .filter(models.HomeDeviceStateModel.room == state.room, models.HomeDeviceStateModel.device == str(state.device))
        .first()
    )
    if obj is None:
        obj = models.HomeDeviceStateModel(
            state_id=state.state_id,
            elder_id=state.elder_id,
            room=state.room,
            device=str(state.device),
        )
        db.add(obj)
    obj.state = state.state
    obj.value = _json(state.value) if state.value is not None else None
    obj.online = state.online
    obj.timestamp = state.timestamp
    obj.raw_json = _json(state)
    db.commit()
    db.refresh(obj)
    return obj


def list_events(db: Session, limit: int = 100) -> list[dict[str, Any]]:
    rows = db.query(models.RiskEventModel).order_by(desc(models.RiskEventModel.created_at)).limit(limit).all()
    return [row_to_dict(row) for row in rows]


def list_devices(db: Session) -> list[dict[str, Any]]:
    rows = db.query(models.HomeDeviceStateModel).order_by(models.HomeDeviceStateModel.room, models.HomeDeviceStateModel.device).all()
    return [row_to_dict(row) for row in rows]


def latest_vital(db: Session, elder_id: str) -> dict[str, Any] | None:
    row = (
        db.query(models.SensorVitalSampleModel)
        .filter(models.SensorVitalSampleModel.elder_id == elder_id)
        .order_by(desc(models.SensorVitalSampleModel.timestamp))
        .first()
    )
    return row_to_dict(row) if row else None


def latest_env(db: Session, elder_id: str) -> dict[str, Any] | None:
    row = (
        db.query(models.SensorEnvSampleModel)
        .filter(models.SensorEnvSampleModel.elder_id == elder_id)
        .order_by(desc(models.SensorEnvSampleModel.timestamp))
        .first()
    )
    return row_to_dict(row) if row else None


def recent_vision(db: Session, elder_id: str, limit: int = 5) -> list[dict[str, Any]]:
    rows = (
        db.query(models.VisionEventModel)
        .filter(models.VisionEventModel.elder_id == elder_id)
        .order_by(desc(models.VisionEventModel.timestamp))
        .limit(limit)
        .all()
    )
    return [row_to_dict(row) for row in rows]


def recent_agent_runs(db: Session, elder_id: str, limit: int = 20) -> list[dict[str, Any]]:
    rows = (
        db.query(models.AgentRunModel)
        .filter(models.AgentRunModel.elder_id == elder_id)
        .order_by(desc(models.AgentRunModel.created_at))
        .limit(limit)
        .all()
    )
    return [row_to_dict(row) for row in rows]


def recent_alerts(db: Session, elder_id: str, limit: int = 20) -> list[dict[str, Any]]:
    rows = (
        db.query(models.AlertRecordModel)
        .filter(models.AlertRecordModel.elder_id == elder_id)
        .order_by(desc(models.AlertRecordModel.timestamp))
        .limit(limit)
        .all()
    )
    return [row_to_dict(row) for row in rows]


def dashboard_state(db: Session, elder_id: str) -> dict[str, Any]:
    events = list_events(db, limit=50)
    latest_event = events[0] if events else None
    return {
        "elder_id": elder_id,
        "elder_status": "正常" if not latest_event or latest_event["risk_level"] == "P4" else "注意",
        "current_risk_level": latest_event["risk_level"] if latest_event else "P4",
        "latest_vital": latest_vital(db, elder_id),
        "latest_env": latest_env(db, elder_id),
        "recent_vision": recent_vision(db, elder_id),
        "events": events,
        "agent_runs": recent_agent_runs(db, elder_id),
        "alerts": recent_alerts(db, elder_id),
        "devices": list_devices(db),
    }

