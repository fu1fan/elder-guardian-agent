from __future__ import annotations

from typing import Any

import yaml

from guardian_shared.schemas import RiskEvent
from guardian_shared.utils import model_to_dict

from app.config import settings
from app.db import crud
from app.db.database import SessionLocal
from app.rule_engine.risk_fusion import RuleResult


class ContextBuilder:
    def build(self, risk_event: RiskEvent, rule_result: RuleResult, source_payload: dict[str, Any]) -> dict[str, Any]:
        with SessionLocal() as db:
            context = {
                "elder_profile": self._load_profile(),
                "current_event": model_to_dict(risk_event),
                "source_payload": source_payload,
                "rule_result": {
                    "event_type": str(rule_result.event_type),
                    "risk_level": rule_result.risk_level.value,
                    "risk_score": rule_result.risk_score,
                    "summary": rule_result.summary,
                    "source": rule_result.source,
                    "room": rule_result.room,
                    "trace": rule_result.trace,
                },
                "recent_vital": crud.latest_vital(db, risk_event.elder_id),
                "recent_environment": crud.latest_env(db, risk_event.elder_id),
                "vision_summary": crud.recent_vision(db, risk_event.elder_id, limit=5),
                "device_states": crud.list_devices(db),
                "historical_risk_events": crud.list_events(db, limit=10),
            }
        return context

    def _load_profile(self) -> dict[str, Any]:
        path = settings.config_dir / "elder_profile.yaml"
        if not path.exists():
            path = settings.config_dir / "elder_profile.example.yaml"
        if not path.exists():
            return {"elder_id": settings.elder_id}
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {"elder_id": settings.elder_id}

