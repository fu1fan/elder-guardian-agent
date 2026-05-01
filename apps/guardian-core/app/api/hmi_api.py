from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from guardian_shared.schemas import HmiResponse

from app.config import settings
from app.db import crud
from app.db.database import SessionLocal

router = APIRouter()


def normalize_response_type(text: str) -> str:
    if text in {"我没事", "safe"}:
        return "safe"
    if text in {"需要帮助", "help"}:
        return "help"
    if text in {"联系家属", "contact_family"}:
        return "contact_family"
    return text


@router.post("/api/hmi/response")
async def hmi_response(payload: dict, request: Request) -> dict:
    response_text = payload.get("response_text") or payload.get("response_type") or "我没事"
    response_type = normalize_response_type(payload.get("response_type") or response_text)
    event_id = payload.get("event_id")
    prompt_id = payload.get("prompt_id")
    if event_id and not prompt_id:
        with SessionLocal() as db:
            prompt = crud.latest_waiting_prompt_for_event(db, event_id)
            if prompt:
                prompt_id = prompt.prompt_id
    if not event_id or not prompt_id:
        raise HTTPException(status_code=400, detail="event_id and prompt_id are required unless event_id has a waiting prompt")
    response = HmiResponse(
        prompt_id=prompt_id,
        event_id=event_id,
        elder_id=payload.get("elder_id", settings.elder_id),
        response_type=response_type,
        response_text=response_text,
    )
    result = await request.app.state.hmi_service.process_response(response)
    return {"ok": True, **result}
