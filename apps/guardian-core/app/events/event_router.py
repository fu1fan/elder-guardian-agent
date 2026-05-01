from __future__ import annotations

import logging
from typing import Any

from guardian_shared.schemas import HmiResponse, HomeDeviceState, SensorEnvSample, SensorVitalSample, VisionEvent
from guardian_shared.utils import parse_json_payload

logger = logging.getLogger(__name__)


class EventRouter:
    def __init__(self) -> None:
        self.sensor_service: Any = None
        self.vision_service: Any = None
        self.home_service: Any = None
        self.hmi_service: Any = None

    async def handle_mqtt_message(self, topic: str, payload: bytes) -> None:
        data = parse_json_payload(payload)
        parts = topic.split("/")
        try:
            if len(parts) >= 4 and parts[0] == "elder" and parts[2] == "sensor" and parts[3] == "vital":
                await self.sensor_service.process_vital(SensorVitalSample(**data))
            elif len(parts) >= 4 and parts[0] == "elder" and parts[2] == "sensor" and parts[3] == "env":
                await self.sensor_service.process_env(SensorEnvSample(**data))
            elif len(parts) >= 3 and parts[0] == "elder" and parts[2] == "vision":
                await self.vision_service.process_vision_event(VisionEvent(**data))
            elif len(parts) >= 4 and parts[0] == "elder" and parts[2] == "hmi" and parts[3] == "response":
                await self.hmi_service.process_response(HmiResponse(**data))
            elif len(parts) >= 4 and parts[0] == "home" and parts[3] == "state":
                await self.home_service.process_device_state(HomeDeviceState(**data))
            elif len(parts) >= 4 and parts[0] == "home" and parts[3] == "ack":
                await self.home_service.process_device_ack(room=parts[1], device=parts[2], payload=data)
            else:
                logger.warning("Unhandled MQTT topic %s", topic)
        except Exception:
            logger.exception("Failed to route MQTT topic=%s payload=%s", topic, data)

