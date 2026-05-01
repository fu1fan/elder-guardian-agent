from __future__ import annotations

import logging
from typing import Any

import httpx

from guardian_shared.enums import EventType, RiskLevel
from guardian_shared.schemas import AgentDecision
from guardian_shared.utils import model_to_dict

from app.agent.prompt_templates import SYSTEM_PROMPT, build_user_prompt
from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self) -> None:
        self.mock = settings.llm_mock

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        if self.mock:
            return model_to_dict(self._mock_decision(context))
        return await self._call_openai_compatible(context)

    def _mock_decision(self, context: dict[str, Any]) -> AgentDecision:
        rule = context.get("rule_result", {})
        risk_level = RiskLevel(rule.get("risk_level", "P4"))
        event_type = rule.get("event_type", EventType.NORMAL.value)
        summary = rule.get("summary", "未发现异常。")
        recommended: list[str]
        need_elder = risk_level in {RiskLevel.P1, RiskLevel.P2}
        need_family = risk_level in {RiskLevel.P0, RiskLevel.P1}
        if risk_level == RiskLevel.P0:
            recommended = ["立即告警", "通知家属", "执行安全联动"]
        elif risk_level == RiskLevel.P1:
            recommended = ["本地询问老人", "同步通知家属", "持续观察"]
        elif risk_level == RiskLevel.P2:
            recommended = ["本地询问老人", "超时升级通知家属"]
        elif risk_level == RiskLevel.P3:
            recommended = ["自动调节环境", "记录事件"]
        else:
            recommended = ["记录正常状态"]
        return AgentDecision(
            risk_level=risk_level,
            risk_score=float(rule.get("risk_score", 0.0)),
            event_type=str(event_type),
            reasoning_summary=summary,
            recommended_actions=recommended,
            need_elder_confirmation=need_elder,
            need_family_notification=need_family,
            alert_priority=risk_level,
            device_actions=[],
        )

    async def _call_openai_compatible(self, context: dict[str, Any]) -> dict[str, Any]:
        url = settings.llm_base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(context)},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
        logger.info("LLM response received")
        return {"raw": content}

