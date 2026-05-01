from __future__ import annotations

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.get("/api/dashboard/state")
async def dashboard_state(request: Request) -> dict:
    return request.app.state.report_service.dashboard_state()


@router.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket) -> None:
    manager = websocket.app.state.websocket_manager
    await manager.connect(websocket)
    try:
        await manager.broadcast("dashboard_state", websocket.app.state.report_service.dashboard_state())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)

