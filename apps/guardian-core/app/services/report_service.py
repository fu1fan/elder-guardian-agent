from __future__ import annotations

from typing import Any

from app.config import settings
from app.db import crud
from app.db.database import SessionLocal


class ReportService:
    def dashboard_state(self) -> dict[str, Any]:
        with SessionLocal() as db:
            return crud.dashboard_state(db, settings.elder_id)

    def events(self, limit: int = 100) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            return crud.list_events(db, limit=limit)

