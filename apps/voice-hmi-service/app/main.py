from __future__ import annotations

import argparse
import json
import os
from typing import Any

import paho.mqtt.client as mqtt

from guardian_shared.schemas import HmiResponse
from guardian_shared.topics import elder_hmi_prompt, elder_hmi_response
from guardian_shared.utils import model_to_json

from app.asr import normalize_reply
from app.tts import speak

LAST_PROMPT: dict[str, Any] | None = None


def publish_reply(client: mqtt.Client, elder_id: str, prompt: dict[str, Any], reply_text: str) -> None:
    response_type, normalized_text = normalize_reply(reply_text)
    response = HmiResponse(
        prompt_id=prompt["prompt_id"],
        event_id=prompt["event_id"],
        elder_id=elder_id,
        response_type=response_type,
        response_text=normalized_text,
    )
    client.publish(elder_hmi_response(elder_id), model_to_json(response), qos=1)
    print(f"[MOCK ASR] reply published: {model_to_json(response)}")


def subscribe(elder_id: str, host: str, port: int) -> None:
    client = mqtt.Client(client_id=f"voice-hmi-{elder_id}")

    def on_connect(client: mqtt.Client, userdata: object, flags: dict, rc: int, properties: object = None) -> None:
        client.subscribe(elder_hmi_prompt(elder_id), qos=1)
        print(f"voice-hmi subscribed {elder_hmi_prompt(elder_id)}")

    def on_message(client: mqtt.Client, userdata: object, msg: mqtt.MQTTMessage) -> None:
        global LAST_PROMPT
        LAST_PROMPT = json.loads(msg.payload.decode("utf-8"))
        speak(LAST_PROMPT["message"])
        print("输入 1=我没事, 2=需要帮助, 3=联系家属 后回车：")

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host, port, keepalive=60)
    client.loop_start()
    try:
        while True:
            text = input("> ").strip()
            if not text:
                continue
            if LAST_PROMPT is None:
                print("还没有收到 HMI prompt。")
                continue
            publish_reply(client, elder_id, LAST_PROMPT, text)
    finally:
        client.loop_stop()
        client.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock voice HMI service.")
    parser.add_argument("--elder-id", default=os.getenv("ELDER_ID", "elder_001"))
    parser.add_argument("--host", default=os.getenv("MQTT_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    args = parser.parse_args()
    subscribe(args.elder_id, args.host, args.port)


if __name__ == "__main__":
    main()

