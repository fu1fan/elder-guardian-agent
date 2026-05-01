#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import paho.mqtt.client as mqtt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "guardian-shared"))

from guardian_shared.schemas import SensorEnvSample, SensorVitalSample
from guardian_shared.topics import elder_sensor_env, elder_sensor_vital
from guardian_shared.utils import model_to_json


def publish(client: mqtt.Client, topic: str, payload: object) -> None:
    body = model_to_json(payload)
    print(f"publish {topic}: {body}")
    client.publish(topic, body, qos=1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish simulated elder sensor samples to MQTT.")
    parser.add_argument("--event", choices=["normal", "spo2_low", "heart_rate_abnormal", "co2_high", "gas_leak"], required=True)
    parser.add_argument("--elder-id", default=os.getenv("ELDER_ID", "elder_001"))
    parser.add_argument("--host", default=os.getenv("MQTT_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    args = parser.parse_args()

    client = mqtt.Client(client_id=f"simulate-sensor-{args.event}")
    client.connect(args.host, args.port, keepalive=30)

    if args.event == "normal":
        publish(
            client,
            elder_sensor_vital(args.elder_id),
            SensorVitalSample(elder_id=args.elder_id, heart_rate=76, spo2=96, systolic_bp=126, diastolic_bp=78, body_temperature=36.5),
        )
        publish(
            client,
            elder_sensor_env(args.elder_id),
            SensorEnvSample(elder_id=args.elder_id, room="living_room", temperature=24.5, humidity=48, co2_ppm=700, gas_ppm=0),
        )
    elif args.event == "spo2_low":
        publish(
            client,
            elder_sensor_vital(args.elder_id),
            SensorVitalSample(elder_id=args.elder_id, heart_rate=92, spo2=86, systolic_bp=138, diastolic_bp=84, body_temperature=36.8),
        )
    elif args.event == "heart_rate_abnormal":
        publish(
            client,
            elder_sensor_vital(args.elder_id),
            SensorVitalSample(elder_id=args.elder_id, heart_rate=124, spo2=95, systolic_bp=142, diastolic_bp=86, body_temperature=36.7),
        )
    elif args.event == "co2_high":
        publish(
            client,
            elder_sensor_env(args.elder_id),
            SensorEnvSample(elder_id=args.elder_id, room="living_room", temperature=25.0, humidity=50, co2_ppm=1900, gas_ppm=0),
        )
    elif args.event == "gas_leak":
        publish(
            client,
            elder_sensor_env(args.elder_id),
            SensorEnvSample(elder_id=args.elder_id, room="kitchen", temperature=25.0, humidity=52, co2_ppm=820, gas_ppm=180),
        )

    client.disconnect()


if __name__ == "__main__":
    main()

