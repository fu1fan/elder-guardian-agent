from __future__ import annotations

import asyncio
import logging
from typing import Any

from guardian_shared.enums import EventState, RiskLevel
from guardian_shared.schemas import HmiPrompt, HmiResponse, RiskEvent
from guardian_shared.utils import model_to_dict

from app.action.escalation_policy import timeout_escalation_level
from app.config import settings
from app.db import crud
from app.db.database import SessionLocal
from app.gateways.hmi_gateway import HmiGateway
from app.gateways.websocket_gateway import WebSocketManager

logger = logging.getLogger(__name__)


class HmiService:
    def __init__(
        self,
        *,
        hmi_gateway: HmiGateway,
        websocket_manager: WebSocketManager,
        alert_service: Any,
    ) -> None:
        self.hmi_gateway = hmi_gateway
        self.websocket_manager = websocket_manager
        self.alert_service = alert_service
        self._timeout_tasks: dict[str, asyncio.Task[None]] = {}

    async def send_prompt(self, risk_event: RiskEvent, message: str) -> HmiPrompt:
        prompt = HmiPrompt(
            event_id=risk_event.event_id,
            elder_id=risk_event.elder_id,
            risk_level=risk_event.risk_level,
            event_type=str(risk_event.event_type),
            message=f"{message} 您现在安全吗？",
            timeout_sec=settings.hmi_response_timeout_sec,
        ).with_expiry()
        with SessionLocal() as db:
            crud.create_hmi_prompt(db, prompt)
            crud.update_risk_event_state(db, risk_event.event_id, EventState.WAIT_RESPONSE)
        self.hmi_gateway.publish_prompt(prompt)
        await self.websocket_manager.broadcast("hmi_prompt", model_to_dict(prompt))
        self._timeout_tasks[prompt.prompt_id] = asyncio.create_task(self._wait_for_timeout(prompt))
        return prompt

    async def process_response(self, response: HmiResponse) -> dict[str, Any]:
        logger.info("HMI response prompt=%s type=%s", response.prompt_id, response.response_type)
        with SessionLocal() as db:
            crud.create_hmi_response(db, response)
            prompt = crud.update_hmi_prompt_status(db, response.prompt_id, "responded", responded_at=response.timestamp)
            risk_row = crud.get_risk_event(db, response.event_id)
            if risk_row is None:
                return {"status": "ignored", "reason": "event_not_found"}
            risk_event = RiskEvent(**crud.row_to_dict(risk_row))
            if response.response_type in {"safe", "我没事"}:
                crud.update_risk_event_state(db, response.event_id, EventState.RESOLVED)
                result = {"status": "resolved", "prompt_id": response.prompt_id, "event_id": response.event_id}
            else:
                crud.update_risk_event_state(db, response.event_id, EventState.FAMILY_ALERT)
                result = {"status": "family_alert", "prompt_id": response.prompt_id, "event_id": response.event_id}
        task = self._timeout_tasks.pop(response.prompt_id, None)
        if task:
            task.cancel()
        await self.websocket_manager.broadcast("hmi_response", model_to_dict(response))
        if result["status"] == "resolved":
            await self.websocket_manager.broadcast("event_state", {"event_id": response.event_id, "state": EventState.RESOLVED.value})
        else:
            await self.alert_service.notify_family(
                risk_event=risk_event,
                priority=RiskLevel.P1,
                message=f"老人回复：{response.response_text}",
            )
        return result

    async def _wait_for_timeout(self, prompt: HmiPrompt) -> None:
        try:
            await asyncio.sleep(prompt.timeout_sec)
        except asyncio.CancelledError:
            return
        with SessionLocal() as db:
            row = crud.get_hmi_prompt(db, prompt.prompt_id)
            if row is None or row.status != "waiting":
                return
            crud.update_hmi_prompt_status(db, prompt.prompt_id, "timeout")
            risk_row = crud.get_risk_event(db, prompt.event_id)
            if risk_row is None:
                return
            new_level = timeout_escalation_level(risk_row.risk_level)
            crud.update_risk_event_state(
                db,
                prompt.event_id,
                EventState.ESCALATED,
                risk_level=new_level.value,
                summary=f"{risk_row.summary} 老人未在 {prompt.timeout_sec} 秒内响应，已升级。",
            )
            risk_event = RiskEvent(**crud.row_to_dict(risk_row))
        await self.websocket_manager.broadcast(
            "hmi_timeout",
            {"prompt_id": prompt.prompt_id, "event_id": prompt.event_id, "risk_level": new_level.value},
        )
        await self.alert_service.notify_family(
            risk_event=risk_event,
            priority=new_level,
            message=f"老人未响应本地询问：{prompt.message}",
        )

