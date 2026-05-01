from __future__ import annotations

import logging
from typing import Any

from guardian_shared.enums import DeviceAction, DeviceType, RiskLevel
from guardian_shared.schemas import HomeDeviceCommand, HomeDeviceState
from guardian_shared.topics import home_device_set
from guardian_shared.utils import model_to_dict

from app.action.device_policy import DevicePolicy
from app.config import settings
from app.db import crud
from app.db.database import SessionLocal
from app.gateways.mqtt_gateway import MqttGateway
from app.gateways.websocket_gateway import WebSocketManager

logger = logging.getLogger(__name__)


DEFAULT_DEVICES = [
    ("living_room", DeviceType.WINDOW, "closed"),
    ("living_room", DeviceType.AIR_CONDITIONER, "off"),
    ("living_room", DeviceType.FAN, "off"),
    ("bedroom", DeviceType.LIGHT, "off"),
    ("kitchen", DeviceType.GAS_VALVE, "open"),
    ("local", DeviceType.LOCAL_ALARM, "off"),
]


class HomeService:
    def __init__(
        self,
        *,
        mqtt_gateway: MqttGateway,
        websocket_manager: WebSocketManager,
        device_policy: DevicePolicy,
    ) -> None:
        self.mqtt_gateway = mqtt_gateway
        self.websocket_manager = websocket_manager
        self.device_policy = device_policy

    def ensure_default_states(self) -> None:
        with SessionLocal() as db:
            for room, device, state in DEFAULT_DEVICES:
                crud.upsert_device_state(
                    db,
                    HomeDeviceState(
                        elder_id=settings.elder_id,
                        room=room,
                        device=device,
                        state=state,
                        value=None,
                        online=True,
                    ),
                )

    async def command_device(self, command: HomeDeviceCommand) -> dict[str, Any]:
        allowed, reason = self.device_policy.is_allowed(command)
        status = "sent" if allowed else "denied"
        with SessionLocal() as db:
            crud.create_device_command(db, command, event_id=None, status=status)
        data = model_to_dict(command)
        data["status"] = status
        if allowed:
            self.mqtt_gateway.publish(home_device_set(command.room, str(command.device)), command)
            await self.websocket_manager.broadcast("device_command", data)
        else:
            data["deny_reason"] = reason
            await self.websocket_manager.broadcast("device_command_denied", data)
        return data

    async def process_device_state(self, state: HomeDeviceState) -> None:
        logger.info("Device state %s/%s=%s", state.room, state.device, state.state)
        with SessionLocal() as db:
            crud.upsert_device_state(db, state)
        await self.websocket_manager.broadcast("device_state", model_to_dict(state))

    async def process_device_ack(self, *, room: str, device: str, payload: dict[str, Any]) -> None:
        logger.info("Device ack %s/%s payload=%s", room, device, payload)
        cmd_id = payload.get("cmd_id")
        if cmd_id:
            with SessionLocal() as db:
                crud.mark_device_command_ack(db, cmd_id, status=payload.get("status", "acked"))
        await self.websocket_manager.broadcast("device_ack", {"room": room, "device": device, **payload})

    @staticmethod
    def build_manual_command(room: str, device: str, action: str, value: Any = None, reason: str = "Dashboard manual control") -> HomeDeviceCommand:
        return HomeDeviceCommand(
            elder_id=settings.elder_id,
            room=room,
            device=device,
            action=action or DeviceAction.TURN_ON,
            value=value,
            reason=reason,
            priority=RiskLevel.P3,
        )

