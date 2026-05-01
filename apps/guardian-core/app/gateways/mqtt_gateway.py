from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import paho.mqtt.client as mqtt

from guardian_shared.topics import ELDER_TOPIC_PATTERNS, HOME_TOPIC_PATTERNS
from guardian_shared.utils import model_to_json

from app.config import settings

logger = logging.getLogger(__name__)
MqttHandler = Callable[[str, bytes], Awaitable[None]]


class MqttGateway:
    def __init__(self, handler: MqttHandler | None = None) -> None:
        self.handler = handler
        self.loop: asyncio.AbstractEventLoop | None = None
        self.connected = False
        self.client = mqtt.Client(client_id=f"guardian-core-{settings.elder_id}")
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def set_handler(self, handler: MqttHandler) -> None:
        self.handler = handler

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        try:
            self.client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
            self.client.loop_start()
            logger.info("MQTT connecting to %s:%s", settings.mqtt_host, settings.mqtt_port)
        except Exception:
            logger.exception("MQTT broker unavailable; HTTP APIs still run")

    def stop(self) -> None:
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            logger.exception("MQTT shutdown failed")

    def publish(self, topic: str, payload: Any) -> bool:
        body = model_to_json(payload)
        logger.info("MQTT publish %s %s", topic, body)
        if not self.connected:
            logger.warning("MQTT not connected; skipped publish to %s", topic)
            return False
        result = self.client.publish(topic, body, qos=1)
        return result.rc == mqtt.MQTT_ERR_SUCCESS

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: dict[str, Any], rc: int, properties: Any = None) -> None:
        self.connected = rc == 0
        if rc == 0:
            logger.info("MQTT connected")
            for topic in [*ELDER_TOPIC_PATTERNS, *HOME_TOPIC_PATTERNS]:
                client.subscribe(topic, qos=1)
                logger.info("MQTT subscribed %s", topic)
        else:
            logger.error("MQTT connect failed rc=%s", rc)

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int, properties: Any = None) -> None:
        self.connected = False
        logger.warning("MQTT disconnected rc=%s", rc)

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        logger.info("MQTT message %s", msg.topic)
        if self.handler is None or self.loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.handler(msg.topic, msg.payload), self.loop)

