from __future__ import annotations

from fastapi import APIRouter, Request

from guardian_shared.schemas import SensorEnvSample, SensorVitalSample

router = APIRouter()


@router.post("/api/sensor/simulate/vital")
async def simulate_vital(sample: SensorVitalSample, request: Request) -> dict:
    event = await request.app.state.sensor_service.process_vital(sample)
    return {"ok": True, "event": event.model_dump(mode="json")}


@router.post("/api/sensor/simulate/env")
async def simulate_env(sample: SensorEnvSample, request: Request) -> dict:
    event = await request.app.state.sensor_service.process_env(sample)
    return {"ok": True, "event": event.model_dump(mode="json")}

