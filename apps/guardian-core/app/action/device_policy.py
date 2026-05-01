from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from guardian_shared.schemas import HomeDeviceCommand

from app.config import settings

logger = logging.getLogger(__name__)


class DevicePolicy:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (settings.config_dir / "device_policy.yaml")
        self.policy = self._load_policy()

    def _load_policy(self) -> dict[str, Any]:
        if not self.path.exists():
            logger.warning("Device policy file not found: %s", self.path)
            return {}
        with self.path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}

    def is_allowed(self, command: HomeDeviceCommand, event_type: str | None = None) -> tuple[bool, str]:
        key = f"{command.room}/{command.device}"
        device_rule = self.policy.get("devices", {}).get(key)
        if device_rule is None:
            return False, f"设备未在策略中登记: {key}"
        if str(command.action) not in set(device_rule.get("allowed_actions", [])):
            return False, f"设备 {key} 不允许动作 {command.action}"
        if event_type:
            event_rule = self.policy.get("event_constraints", {}).get(event_type, {})
            denied = set(event_rule.get("denied_devices", []))
            allowed = set(event_rule.get("allowed_devices", []))
            if key in denied:
                return False, f"{event_type} 场景禁止控制 {key}"
            if allowed and key not in allowed:
                return False, f"{event_type} 场景不允许控制 {key}"
        return True, "allowed"

    def filter_commands(
        self,
        commands: list[HomeDeviceCommand],
        event_type: str | None = None,
    ) -> tuple[list[HomeDeviceCommand], list[dict[str, str]]]:
        allowed: list[HomeDeviceCommand] = []
        denied: list[dict[str, str]] = []
        for command in commands:
            ok, reason = self.is_allowed(command, event_type=event_type)
            if ok:
                allowed.append(command)
            else:
                denied.append(
                    {
                        "cmd_id": command.cmd_id,
                        "room": command.room,
                        "device": str(command.device),
                        "action": str(command.action),
                        "reason": reason,
                    }
                )
                logger.warning("Device command denied: %s", denied[-1])
        return allowed, denied

