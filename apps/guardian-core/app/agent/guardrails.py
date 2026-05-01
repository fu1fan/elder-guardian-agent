from __future__ import annotations

from guardian_shared.enums import EventType, RiskLevel
from guardian_shared.schemas import AgentDecision

from app.rule_engine.risk_fusion import RISK_ORDER, RuleResult


class Guardrails:
    def enforce(self, decision: AgentDecision, rule_result: RuleResult) -> AgentDecision:
        rule_level = rule_result.risk_level
        decision_level = RiskLevel(decision.risk_level)
        if rule_level == RiskLevel.P0 and decision_level != RiskLevel.P0:
            decision = decision.model_copy(update={"risk_level": RiskLevel.P0, "alert_priority": RiskLevel.P0})
        if rule_level == RiskLevel.P1 and RISK_ORDER[decision_level] > RISK_ORDER[RiskLevel.P2]:
            decision = decision.model_copy(update={"risk_level": RiskLevel.P1, "alert_priority": RiskLevel.P1})
        if str(rule_result.event_type) == EventType.GAS_LEAK.value:
            allowed = {"window", "gas_valve", "local_alarm"}
            filtered = [
                item
                for item in decision.device_actions
                if str(item.get("device", "")) in allowed
            ]
            decision = decision.model_copy(
                update={
                    "risk_level": RiskLevel.P0,
                    "alert_priority": RiskLevel.P0,
                    "need_elder_confirmation": False,
                    "need_family_notification": True,
                    "device_actions": filtered,
                }
            )
        return decision

