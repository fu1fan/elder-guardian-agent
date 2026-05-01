from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from guardian_shared.schemas import RiskEvent

from app.db import crud
from app.db.database import SessionLocal
from app.rule_engine.risk_fusion import RuleResult

router = APIRouter()


@router.post("/api/agent/analyze")
async def analyze_existing_event(payload: dict, request: Request) -> dict:
    event_id = payload.get("event_id")
    if not event_id:
        raise HTTPException(status_code=400, detail="event_id is required for MVP analyze endpoint")
    with SessionLocal() as db:
        row = crud.get_risk_event(db, event_id)
        if row is None:
            raise HTTPException(status_code=404, detail="event not found")
        risk_event = RiskEvent(**crud.row_to_dict(row))
    rule_result = RuleResult(
        event_type=risk_event.event_type,
        risk_level=risk_event.risk_level,
        risk_score=risk_event.risk_score,
        summary=risk_event.summary,
        source=risk_event.source,
        room=risk_event.room,
        trace=risk_event.rule_trace,
    )
    await request.app.state.agent_runtime.handle_event(risk_event, rule_result, payload)
    return {"ok": True, "event_id": event_id}

