from __future__ import annotations

from typing import Any

from guardian_shared.enums import DeviceAction, DeviceType, EventType, RiskLevel
from guardian_shared.schemas import HomeDeviceCommand


def suggest_device_commands(
    *,
    elder_id: str,
    event_type: str,
    risk_level: str,
    reason: str,
) -> list[HomeDeviceCommand]:
    priority = RiskLevel(risk_level)
    commands: list[HomeDeviceCommand] = []
    if event_type == EventType.CO2_HIGH.value:
        commands.append(
            HomeDeviceCommand(
                elder_id=elder_id,
                room="living_room",
                device=DeviceType.WINDOW,
                action=DeviceAction.OPEN,
                value=None,
                reason=reason or "室内 CO2 偏高，自动开窗通风。",
                priority=priority,
            )
        )
    elif event_type == EventType.TEMPERATURE_HIGH.value:
        commands.extend(
            [
                HomeDeviceCommand(
                    elder_id=elder_id,
                    room="living_room",
                    device=DeviceType.AIR_CONDITIONER,
                    action=DeviceAction.SET_TEMPERATURE,
                    value=26,
                    reason=reason or "室温偏高，自动调低空调目标温度。",
                    priority=priority,
                ),
                HomeDeviceCommand(
                    elder_id=elder_id,
                    room="living_room",
                    device=DeviceType.FAN,
                    action=DeviceAction.TURN_ON,
                    value=None,
                    reason=reason or "室温偏高，打开风扇辅助通风。",
                    priority=priority,
                ),
            ]
        )
    elif event_type == EventType.TEMPERATURE_LOW.value:
        commands.append(
            HomeDeviceCommand(
                elder_id=elder_id,
                room="living_room",
                device=DeviceType.AIR_CONDITIONER,
                action=DeviceAction.SET_TEMPERATURE,
                value=24,
                reason=reason or "室温偏低，自动提高空调目标温度。",
                priority=priority,
            )
        )
    elif event_type == EventType.NIGHT_ABNORMAL_ACTIVITY.value:
        commands.append(
            HomeDeviceCommand(
                elder_id=elder_id,
                room="bedroom",
                device=DeviceType.LIGHT,
                action=DeviceAction.TURN_ON,
                value=None,
                reason=reason or "夜间活动，自动开启卧室灯光。",
                priority=priority,
            )
        )
    elif event_type == EventType.GAS_LEAK.value:
        commands.extend(_gas_leak_commands(elder_id, priority, reason))
    return commands


def _gas_leak_commands(elder_id: str, priority: RiskLevel, reason: str) -> list[HomeDeviceCommand]:
    base_reason = reason or "燃气泄漏 P0，执行安全联动。"
    specs: list[dict[str, Any]] = [
        {"room": "living_room", "device": DeviceType.WINDOW, "action": DeviceAction.OPEN, "reason": "燃气泄漏，打开窗户通风。"},
        {"room": "kitchen", "device": DeviceType.GAS_VALVE, "action": DeviceAction.CLOSE, "reason": "燃气泄漏，关闭燃气阀门。"},
        {"room": "local", "device": DeviceType.LOCAL_ALARM, "action": DeviceAction.ALARM_ON, "reason": "燃气泄漏，启动本地声光报警。"},
    ]
    return [
        HomeDeviceCommand(
            elder_id=elder_id,
            room=str(item["room"]),
            device=item["device"],
            action=item["action"],
            value=None,
            reason=f"{base_reason} {item['reason']}",
            priority=priority,
        )
        for item in specs
    ]

