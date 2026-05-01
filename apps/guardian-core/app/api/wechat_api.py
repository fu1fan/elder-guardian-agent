from __future__ import annotations

import logging

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/wechat/message")
async def wechat_message(payload: dict, request: Request) -> dict:
    text = payload.get("text") or payload.get("message") or ""
    logger.info("[MOCK WECHAT INBOUND] %s", text)
    state = request.app.state.report_service.dashboard_state()
    if "为什么" in text or "报警" in text:
        latest = state.get("events", [{}])[0] if state.get("events") else {}
        reply = f"最近一次事件：{latest.get('summary', '暂无异常记录')}"
    elif "今天" in text or "异常" in text:
        reply = f"今日 MVP 已记录 {len(state.get('events', []))} 条风险/状态事件。"
    else:
        reply = f"老人当前状态：{state.get('elder_status')}，风险等级 {state.get('current_risk_level')}。"
    await request.app.state.websocket_manager.broadcast("wechat_message", {"incoming": payload, "reply": reply})
    return {"ok": True, "reply": reply}

