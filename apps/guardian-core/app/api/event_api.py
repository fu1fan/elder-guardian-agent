from __future__ import annotations

from fastapi import APIRouter, Query, Request

from guardian_shared.schemas import VisionEvent

router = APIRouter()


@router.get("/api/events")
async def list_events(request: Request, limit: int = Query(100, ge=1, le=500)) -> dict:
    return {"events": request.app.state.report_service.events(limit=limit)}


@router.post("/api/vision/simulate")
async def simulate_vision(event: VisionEvent, request: Request) -> dict:
    risk_event = await request.app.state.vision_service.process_vision_event(event)
    return {"ok": True, "event": risk_event.model_dump(mode="json")}

