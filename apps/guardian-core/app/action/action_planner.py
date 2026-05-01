from __future__ import annotations

from dataclasses import dataclass, field

from guardian_shared.enums import ActionType, DeviceAction, DeviceType, EventType, RiskLevel
from guardian_shared.schemas import AgentDecision, HomeDeviceCommand, RiskEvent

from app.rule_engine.home_control_rules import suggest_device_commands
from app.rule_engine.risk_fusion import RuleResult


@dataclass
class PlannedAction:
    action_type: ActionType
    message: str = ""
    device_commands: list[HomeDeviceCommand] = field(default_factory=list)


@dataclass
class ActionPlan:
    event_id: str
    risk_level: RiskLevel
    event_type: str
    actions: list[PlannedAction]


class ActionPlanner:
    def plan(self, risk_event: RiskEvent, decision: AgentDecision, rule_result: RuleResult) -> ActionPlan:
        risk_level = RiskLevel(decision.risk_level)
        event_type = str(decision.event_type)
        actions: list[PlannedAction] = []
        reason = decision.reasoning_summary or rule_result.summary

        if risk_level == RiskLevel.P0:
            device_commands = suggest_device_commands(
                elder_id=risk_event.elder_id,
                event_type=event_type,
                risk_level=risk_level.value,
                reason=reason,
            )
            if event_type != EventType.GAS_LEAK.value:
                device_commands.append(
                    HomeDeviceCommand(
                        elder_id=risk_event.elder_id,
                        room="local",
                        device=DeviceType.LOCAL_ALARM,
                        action=DeviceAction.ALARM_ON,
                        value=None,
                        reason="P0 紧急风险，启动本地报警。",
                        priority=RiskLevel.P0,
                    )
                )
            actions.append(PlannedAction(ActionType.EMERGENCY_ALERT, message=reason))
            actions.append(PlannedAction(ActionType.NOTIFY_FAMILY, message=reason))
            if device_commands:
                actions.append(PlannedAction(ActionType.AUTO_CONTROL, message=reason, device_commands=device_commands))
        elif risk_level == RiskLevel.P1:
            actions.append(PlannedAction(ActionType.ASK_ELDER, message=reason))
            actions.append(PlannedAction(ActionType.NOTIFY_FAMILY, message=reason))
        elif risk_level == RiskLevel.P2:
            actions.append(PlannedAction(ActionType.ASK_ELDER, message=reason))
        elif risk_level == RiskLevel.P3:
            device_commands = suggest_device_commands(
                elder_id=risk_event.elder_id,
                event_type=event_type,
                risk_level=risk_level.value,
                reason=reason,
            )
            if device_commands:
                actions.append(PlannedAction(ActionType.AUTO_CONTROL, message=reason, device_commands=device_commands))
            else:
                actions.append(PlannedAction(ActionType.RECORD_ONLY, message=reason))
        else:
            actions.append(PlannedAction(ActionType.RECORD_ONLY, message=reason))

        return ActionPlan(
            event_id=risk_event.event_id,
            risk_level=risk_level,
            event_type=event_type,
            actions=actions,
        )

