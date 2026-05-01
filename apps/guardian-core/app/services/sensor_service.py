from __future__ import annotations

import logging

from guardian_shared.enums import EventState
from guardian_shared.schemas import RiskEvent, SensorEnvSample, SensorVitalSample
from guardian_shared.utils import model_to_dict

from app.db import crud
from app.db.database import SessionLocal
from app.gateways.websocket_gateway import WebSocketManager
from app.rule_engine.env_rules import classify_env
from app.rule_engine.risk_fusion import RuleResult
from app.rule_engine.vital_rules import classify_vital

logger = logging.getLogger(__name__)


class SensorService:
    def __init__(self, *, agent_runtime: object, websocket_manager: WebSocketManager) -> None:
        self.agent_runtime = agent_runtime
        self.websocket_manager = websocket_manager

    async def process_vital(self, sample: SensorVitalSample) -> RiskEvent:
        logger.info("Processing vital sample elder=%s hr=%s spo2=%s", sample.elder_id, sample.heart_rate, sample.spo2)
        with SessionLocal() as db:
            crud.create_vital_sample(db, sample)
        await self.websocket_manager.broadcast("sensor_vital", model_to_dict(sample))
        return await self._handle_rule(sample.elder_id, classify_vital(sample), model_to_dict(sample))

    async def process_env(self, sample: SensorEnvSample) -> RiskEvent:
        logger.info("Processing env sample elder=%s room=%s co2=%s gas=%s", sample.elder_id, sample.room, sample.co2_ppm, sample.gas_ppm)
        with SessionLocal() as db:
            crud.create_env_sample(db, sample)
        await self.websocket_manager.broadcast("sensor_env", model_to_dict(sample))
        return await self._handle_rule(sample.elder_id, classify_env(sample), model_to_dict(sample))

    async def _handle_rule(self, elder_id: str, result: RuleResult, source_payload: dict) -> RiskEvent:
        event = RiskEvent(
            elder_id=elder_id,
            event_type=result.event_type,
            risk_level=result.risk_level,
            risk_score=result.risk_score,
            state=EventState.RULE_CLASSIFIED,
            source=result.source,
            room=result.room,
            summary=result.summary,
            rule_trace=result.trace,
        )
        with SessionLocal() as db:
            crud.create_risk_event(db, event)
        await self.websocket_manager.broadcast("risk_event", model_to_dict(event))
        await self.agent_runtime.handle_event(event, result, source_payload)
        return event

