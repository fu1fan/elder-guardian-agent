#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import paho.mqtt.client as mqtt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "guardian-shared"))

from guardian_shared.enums import EventType
from guardian_shared.schemas import VisionEvent
from guardian_shared.topics import elder_vision_event
from guardian_shared.utils import model_to_json


EVENTS = {
    "suspected_fall": {"confidence": 0.86, "posture": "lying_low", "motion_state": "sudden_down"},
    "long_static": {"confidence": 0.72, "posture": "sitting_or_lying", "motion_state": "static_45min"},
    "night_abnormal_activity": {"confidence": 0.77, "posture": "standing", "motion_state": "night_wandering"},
    "normal": {"confidence": 0.98, "posture": "standing", "motion_state": "normal"},
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish simulated vision events to MQTT.")
    parser.add_argument("--event", choices=list(EVENTS), required=True)
    parser.add_argument("--elder-id", default=os.getenv("ELDER_ID", "elder_001"))
    parser.add_argument("--room", default="living_room")
    parser.add_argument("--host", default=os.getenv("MQTT_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    args = parser.parse_args()

    spec = EVENTS[args.event]
    event = VisionEvent(
        elder_id=args.elder_id,
        room=args.room,
        event_type=EventType(args.event),
        confidence=spec["confidence"],
        posture=spec["posture"],
        motion_state=spec["motion_state"],
        snapshot_path=str(ROOT / "data" / "snapshots" / f"{args.event}.jpg"),
    )
    client = mqtt.Client(client_id=f"simulate-vision-{args.event}")
    client.connect(args.host, args.port, keepalive=30)
    topic = elder_vision_event(args.elder_id)
    body = model_to_json(event)
    print(f"publish {topic}: {body}")
    client.publish(topic, body, qos=1)
    client.disconnect()


if __name__ == "__main__":
    main()

