#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import paho.mqtt.client as mqtt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "guardian-shared"))

from guardian_shared.schemas import HomeDeviceState
from guardian_shared.topics import home_device_ack, home_device_state
from guardian_shared.utils import model_to_json


def derive_state(action: str, value: Any) -> tuple[str, Any]:
    if action == "open":
        return "open", value
    if action == "close":
        return "closed", value
    if action in {"turn_on", "alarm_on"}:
        return "on", value
    if action in {"turn_off", "alarm_off"}:
        return "off", value
    if action == "set_temperature":
        return "on", value
    return "unknown", value


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate smart home devices and publish ack/state.")
    parser.add_argument("--host", default=os.getenv("MQTT_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    args = parser.parse_args()

    client = mqtt.Client(client_id="simulate-device")

    def on_connect(client: mqtt.Client, userdata: object, flags: dict, rc: int, properties: object = None) -> None:
        print(f"connected rc={rc}; subscribe home/+/+/set")
        client.subscribe("home/+/+/set", qos=1)

    def on_message(client: mqtt.Client, userdata: object, msg: mqtt.MQTTMessage) -> None:
        parts = msg.topic.split("/")
        room, device = parts[1], parts[2]
        data = json.loads(msg.payload.decode("utf-8"))
        print(f"[DEVICE] {room}/{device} command: {data}")
        state_text, value = derive_state(str(data.get("action")), data.get("value"))
        ack = {"cmd_id": data.get("cmd_id"), "status": "acked", "room": room, "device": device}
        state = HomeDeviceState(
            elder_id=data.get("elder_id"),
            room=room,
            device=device,
            state=state_text,
            value=value,
            online=True,
        )
        client.publish(home_device_ack(room, device), json.dumps(ack, ensure_ascii=False), qos=1)
        client.publish(home_device_state(room, device), model_to_json(state), qos=1)
        print(f"[DEVICE] ack/state published for {room}/{device}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.host, args.port, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    main()

