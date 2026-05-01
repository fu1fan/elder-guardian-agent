from __future__ import annotations

import logging
from typing import Any

from guardian_shared.enums import EventState, RiskLevel
from guardian_shared.schemas import AgentDecision, AgentRunRecord, RiskEvent
from guardian_shared.topics import elder_agent_decision
from guardian_shared.utils import model_to_dict

from app.action.action_executor import ActionExecutor
from app.action.action_planner import ActionPlanner
from app.agent.context_builder import ContextBuilder
from app.agent.guardrails import Guardrails
from app.agent.llm_client import LLMClient
from app.agent.output_parser import OutputParser
from app.agent.queue import ElderSerialQueue
from app.config import settings
from app.db import crud
from app.db.database import SessionLocal
from app.gateways.mqtt_gateway import MqttGateway
from app.gateways.websocket_gateway import WebSocketManager
from app.rule_engine.risk_fusion import RuleResult

logger = logging.getLogger(__name__)


class GuardianAgentRuntime:
    def __init__(
        self,
        *,
        action_planner: ActionPlanner,
        action_executor: ActionExecutor,
        mqtt_gateway: MqttGateway,
        websocket_manager: WebSocketManager,
    ) -> None:
        self.queue = ElderSerialQueue()
        self.context_builder = ContextBuilder()
        self.llm_client = LLMClient()
        self.output_parser = OutputParser()
        self.guardrails = Guardrails()
        self.action_planner = action_planner
        self.action_executor = action_executor
        self.mqtt_gateway = mqtt_gateway
        self.websocket_manager = websocket_manager

    async def handle_event(self, risk_event: RiskEvent, rule_result: RuleResult, source_payload: dict[str, Any]) -> None:
        await self.queue.run(risk_event.elder_id, lambda: self._handle_event_locked(risk_event, rule_result, source_payload))

    async def _handle_event_locked(self, risk_event: RiskEvent, rule_result: RuleResult, source_payload: dict[str, Any]) -> None:
        logger.info("Agent handling event=%s level=%s type=%s", risk_event.event_id, risk_event.risk_level, risk_event.event_type)
        context = self.context_builder.build(risk_event, rule_result, source_payload)
        if rule_result.risk_level == RiskLevel.P0:
            decision = self._p0_decision(rule_result)
            llm_mock = True
        else:
            try:
                raw_decision = await self.llm_client.analyze(context)
                decision = self.output_parser.parse(raw_decision)
                llm_mock = settings.llm_mock
            except Exception:
                logger.exception("LLM analysis failed; falling back to mock decision")
                raw_decision = model_to_dict(LLMClient()._mock_decision(context))
                decision = self.output_parser.parse(raw_decision)
                llm_mock = True

        decision = self.guardrails.enforce(decision, rule_result)
        with SessionLocal() as db:
            crud.update_risk_event_state(db, risk_event.event_id, EventState.ACTION_PLANNED, risk_level=str(decision.risk_level))
            crud.create_agent_run(
                db,
                AgentRunRecord(
                    event_id=risk_event.event_id,
                    elder_id=risk_event.elder_id,
                    context=context,
                    decision=decision,
                    llm_mock=llm_mock,
                ),
            )
        self.mqtt_gateway.publish(elder_agent_decision(risk_event.elder_id), decision)
        await self.websocket_manager.broadcast(
            "agent_decision",
            {"event_id": risk_event.event_id, **model_to_dict(decision)},
        )
        planned_event = risk_event.model_copy(update={"risk_level": decision.risk_level, "risk_score": decision.risk_score})
        plan = self.action_planner.plan(planned_event, decision, rule_result)
        await self.action_executor.execute(planned_event, plan)

    def _p0_decision(self, rule_result: RuleResult) -> AgentDecision:
        return AgentDecision(
            risk_level=RiskLevel.P0,
            risk_score=max(rule_result.risk_score, 0.95),
            event_type=str(rule_result.event_type),
            reasoning_summary=rule_result.summary,
            recommended_actions=["立即告警", "通知家属", "执行安全设备联动", "记录事件"],
            need_elder_confirmation=False,
            need_family_notification=True,
            alert_priority=RiskLevel.P0,
            device_actions=[],
        )

