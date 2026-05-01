from __future__ import annotations

import logging
from typing import Any

from guardian_shared.enums import ActionType, EventState, RiskLevel
from guardian_shared.schemas import HomeDeviceCommand, RiskEvent
from guardian_shared.topics import home_device_set
from guardian_shared.utils import model_to_dict

from app.action.action_planner import ActionPlan, PlannedAction
from app.action.device_policy import DevicePolicy
from app.db import crud
from app.db.database import SessionLocal
from app.gateways.mqtt_gateway import MqttGateway
from app.gateways.websocket_gateway import WebSocketManager

logger = logging.getLogger(__name__)


class ActionExecutor:
    def __init__(
        self,
        *,
        mqtt_gateway: MqttGateway,
        websocket_manager: WebSocketManager,
        hmi_service: Any,
        alert_service: Any,
        device_policy: DevicePolicy,
    ) -> None:
        self.mqtt_gateway = mqtt_gateway
        self.websocket_manager = websocket_manager
        self.hmi_service = hmi_service
        self.alert_service = alert_service
        self.device_policy = device_policy

    async def execute(self, risk_event: RiskEvent, plan: ActionPlan) -> None:
        for action in plan.actions:
            await self._execute_action(risk_event, plan, action)

    async def _execute_action(self, risk_event: RiskEvent, plan: ActionPlan, action: PlannedAction) -> None:
        logger.info("Executing action %s for event %s", action.action_type, risk_event.event_id)
        if action.action_type == ActionType.AUTO_CONTROL:
            await self._execute_device_commands(risk_event, plan, action.device_commands)
        elif action.action_type == ActionType.ASK_ELDER:
            await self.hmi_service.send_prompt(risk_event, action.message)
        elif action.action_type == ActionType.NOTIFY_FAMILY:
            await self.alert_service.notify_family(
                risk_event=risk_event,
                priority=plan.risk_level,
                message=action.message or risk_event.summary,
            )
        elif action.action_type == ActionType.EMERGENCY_ALERT:
            await self.alert_service.emergency_alert(
                risk_event=risk_event,
                message=action.message or risk_event.summary,
            )
        elif action.action_type == ActionType.RECORD_ONLY:
            await self._record_only(risk_event)

    async def _execute_device_commands(
        self,
        risk_event: RiskEvent,
        plan: ActionPlan,
        commands: list[HomeDeviceCommand],
    ) -> None:
        allowed, denied = self.device_policy.filter_commands(commands, event_type=plan.event_type)
        with SessionLocal() as db:
            if plan.risk_level != RiskLevel.P0:
                crud.update_risk_event_state(db, risk_event.event_id, EventState.AUTO_CONTROL)
            for denied_item in denied:
                await self.websocket_manager.broadcast("device_command_denied", denied_item)
            for command in allowed:
                crud.create_device_command(db, command, event_id=risk_event.event_id)
                topic = home_device_set(command.room, str(command.device))
                self.mqtt_gateway.publish(topic, command)
                await self.websocket_manager.broadcast("device_command", model_to_dict(command))
        if plan.risk_level != RiskLevel.P0:
            await self.websocket_manager.broadcast(
                "event_state",
                {"event_id": risk_event.event_id, "state": EventState.AUTO_CONTROL.value},
            )
        if plan.risk_level in {RiskLevel.P3, RiskLevel.P4}:
            with SessionLocal() as db:
                crud.update_risk_event_state(db, risk_event.event_id, EventState.RECORDED)

    async def _record_only(self, risk_event: RiskEvent) -> None:
        with SessionLocal() as db:
            crud.update_risk_event_state(db, risk_event.event_id, EventState.RECORDED)
        await self.websocket_manager.broadcast(
            "event_state",
            {"event_id": risk_event.event_id, "state": EventState.RECORDED.value},
        )
