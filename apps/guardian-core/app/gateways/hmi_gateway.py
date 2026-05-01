from __future__ import annotations

from guardian_shared.schemas import HmiPrompt
from guardian_shared.topics import elder_hmi_prompt

from app.gateways.mqtt_gateway import MqttGateway


class HmiGateway:
    def __init__(self, mqtt_gateway: MqttGateway) -> None:
        self.mqtt_gateway = mqtt_gateway

    def publish_prompt(self, prompt: HmiPrompt) -> bool:
        return self.mqtt_gateway.publish(elder_hmi_prompt(prompt.elder_id), prompt)

