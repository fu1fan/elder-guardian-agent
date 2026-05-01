from __future__ import annotations

import logging

from guardian_shared.enums import EventState
from guardian_shared.schemas import RiskEvent, VisionEvent
from guardian_shared.utils import model_to_dict

from app.db import crud
from app.db.database import SessionLocal
from app.gateways.websocket_gateway import WebSocketManager
from app.rule_engine.vision_rules import classify_vision

logger = logging.getLogger(__name__)


class VisionService:
    def __init__(self, *, agent_runtime: object, websocket_manager: WebSocketManager) -> None:
        self.agent_runtime = agent_runtime
        self.websocket_manager = websocket_manager

    async def process_vision_event(self, event: VisionEvent) -> RiskEvent:
        logger.info("Processing vision event elder=%s type=%s confidence=%s", event.elder_id, event.event_type, event.confidence)
        with SessionLocal() as db:
            crud.create_vision_event(db, event)
        await self.websocket_manager.broadcast("vision_event", model_to_dict(event))
        result = classify_vision(event)
        risk_event = RiskEvent(
            elder_id=event.elder_id,
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
            crud.create_risk_event(db, risk_event)
        await self.websocket_manager.broadcast("risk_event", model_to_dict(risk_event))
        await self.agent_runtime.handle_event(risk_event, result, model_to_dict(event))
        return risk_event

