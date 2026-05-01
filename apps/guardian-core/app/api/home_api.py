from __future__ import annotations

from fastapi import APIRouter, Request

from guardian_shared.schemas import HomeDeviceCommand

from app.config import settings
from app.db import crud
from app.db.database import SessionLocal

router = APIRouter()


@router.get("/api/home/devices")
async def list_devices() -> dict:
    with SessionLocal() as db:
        return {"devices": crud.list_devices(db)}


@router.post("/api/home/device/command")
async def command_device(payload: dict, request: Request) -> dict:
    if "elder_id" not in payload:
        payload["elder_id"] = settings.elder_id
    if "reason" not in payload:
        payload["reason"] = "Dashboard manual control"
    command = HomeDeviceCommand(**payload)
    result = await request.app.state.home_service.command_device(command)
    return {"ok": result.get("status") == "sent", "command": result}

