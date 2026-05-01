from __future__ import annotations

import json
from typing import Any

from guardian_shared.schemas import AgentDecision


class OutputParser:
    def parse(self, payload: dict[str, Any]) -> AgentDecision:
        if "raw" in payload:
            payload = json.loads(payload["raw"])
        return AgentDecision(**payload)

