from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

from guardian_shared.schemas import DashboardMessage
from guardian_shared.utils import model_to_json

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("WebSocket connected: %s", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("WebSocket disconnected: %s", len(self._connections))

    async def broadcast(self, message_type: str, data: dict[str, Any]) -> None:
        message = DashboardMessage(type=message_type, data=data)
        payload = model_to_json(message)
        async with self._lock:
            targets = list(self._connections)
        for websocket in targets:
            try:
                await websocket.send_text(payload)
            except Exception:
                logger.exception("Failed to send WebSocket message")
                await self.disconnect(websocket)

