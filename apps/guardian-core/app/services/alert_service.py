from __future__ import annotations

import logging

from guardian_shared.enums import EventState, RiskLevel
from guardian_shared.schemas import AlertRecord, RiskEvent
from guardian_shared.topics import elder_alert_event
from guardian_shared.utils import model_to_dict

from app.db import crud
from app.db.database import SessionLocal
from app.gateways.mqtt_gateway import MqttGateway
from app.gateways.wechat_gateway import WechatGateway
from app.gateways.websocket_gateway import WebSocketManager

logger = logging.getLogger(__name__)


class AlertService:
    def __init__(
        self,
        *,
        mqtt_gateway: MqttGateway,
        websocket_manager: WebSocketManager,
        wechat_gateway: WechatGateway,
    ) -> None:
        self.mqtt_gateway = mqtt_gateway
        self.websocket_manager = websocket_manager
        self.wechat_gateway = wechat_gateway

    async def notify_family(self, *, risk_event: RiskEvent, priority: RiskLevel, message: str) -> AlertRecord:
        alert = AlertRecord(
            event_id=risk_event.event_id,
            elder_id=risk_event.elder_id,
            priority=priority,
            channel="mock_wechat",
            message=f"家属通知：{message}",
        )
        with SessionLocal() as db:
            crud.create_alert(db, alert)
        self.mqtt_gateway.publish(elder_alert_event(risk_event.elder_id), alert)
        await self.wechat_gateway.notify_family(alert)
        await self.websocket_manager.broadcast("alert", model_to_dict(alert))
        return alert

    async def emergency_alert(self, *, risk_event: RiskEvent, message: str) -> AlertRecord:
        alert = AlertRecord(
            event_id=risk_event.event_id,
            elder_id=risk_event.elder_id,
            priority=RiskLevel.P0,
            channel="local_emergency",
            message=f"紧急告警：{message}",
        )
        with SessionLocal() as db:
            crud.create_alert(db, alert)
            crud.update_risk_event_state(db, risk_event.event_id, EventState.EMERGENCY_ALERT, risk_level=RiskLevel.P0.value)
        self.mqtt_gateway.publish(elder_alert_event(risk_event.elder_id), alert)
        await self.websocket_manager.broadcast("emergency_alert", model_to_dict(alert))
        return alert

