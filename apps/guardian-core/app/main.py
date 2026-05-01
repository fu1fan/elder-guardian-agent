from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.action.action_executor import ActionExecutor
from app.action.action_planner import ActionPlanner
from app.action.device_policy import DevicePolicy
from app.agent.runtime import GuardianAgentRuntime
from app.api import agent_api, dashboard_api, event_api, hmi_api, home_api, sensor_api, wechat_api
from app.config import settings
from app.db.database import init_db
from app.events.event_router import EventRouter
from app.gateways.hmi_gateway import HmiGateway
from app.gateways.mqtt_gateway import MqttGateway
from app.gateways.wechat_gateway import WechatGateway
from app.gateways.websocket_gateway import WebSocketManager
from app.services.alert_service import AlertService
from app.services.hmi_service import HmiService
from app.services.home_service import HomeService
from app.services.report_service import ReportService
from app.services.sensor_service import SensorService
from app.services.vision_service import VisionService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Elder Guardian Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sensor_api.router)
app.include_router(event_api.router)
app.include_router(agent_api.router)
app.include_router(home_api.router)
app.include_router(dashboard_api.router)
app.include_router(hmi_api.router)
app.include_router(wechat_api.router)


@app.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "app_env": settings.app_env,
        "elder_id": settings.elder_id,
        "mqtt": {"host": settings.mqtt_host, "port": settings.mqtt_port, "connected": app.state.mqtt_gateway.connected},
        "llm_mock": settings.llm_mock,
    }


@app.on_event("startup")
async def startup() -> None:
    init_db()
    websocket_manager = WebSocketManager()
    mqtt_gateway = MqttGateway()
    event_router = EventRouter()
    mqtt_gateway.set_handler(event_router.handle_mqtt_message)
    wechat_gateway = WechatGateway(mock=settings.wechat_mock)
    device_policy = DevicePolicy()
    report_service = ReportService()
    alert_service = AlertService(
        mqtt_gateway=mqtt_gateway,
        websocket_manager=websocket_manager,
        wechat_gateway=wechat_gateway,
    )
    hmi_gateway = HmiGateway(mqtt_gateway)
    hmi_service = HmiService(
        hmi_gateway=hmi_gateway,
        websocket_manager=websocket_manager,
        alert_service=alert_service,
    )
    action_executor = ActionExecutor(
        mqtt_gateway=mqtt_gateway,
        websocket_manager=websocket_manager,
        hmi_service=hmi_service,
        alert_service=alert_service,
        device_policy=device_policy,
    )
    action_planner = ActionPlanner()
    agent_runtime = GuardianAgentRuntime(
        action_planner=action_planner,
        action_executor=action_executor,
        mqtt_gateway=mqtt_gateway,
        websocket_manager=websocket_manager,
    )
    sensor_service = SensorService(agent_runtime=agent_runtime, websocket_manager=websocket_manager)
    vision_service = VisionService(agent_runtime=agent_runtime, websocket_manager=websocket_manager)
    home_service = HomeService(
        mqtt_gateway=mqtt_gateway,
        websocket_manager=websocket_manager,
        device_policy=device_policy,
    )
    home_service.ensure_default_states()

    event_router.sensor_service = sensor_service
    event_router.vision_service = vision_service
    event_router.home_service = home_service
    event_router.hmi_service = hmi_service

    app.state.websocket_manager = websocket_manager
    app.state.mqtt_gateway = mqtt_gateway
    app.state.event_router = event_router
    app.state.agent_runtime = agent_runtime
    app.state.sensor_service = sensor_service
    app.state.vision_service = vision_service
    app.state.home_service = home_service
    app.state.hmi_service = hmi_service
    app.state.alert_service = alert_service
    app.state.report_service = report_service

    mqtt_gateway.start(asyncio.get_running_loop())
    logger.info("Guardian core started for elder_id=%s", settings.elder_id)


@app.on_event("shutdown")
async def shutdown() -> None:
    app.state.mqtt_gateway.stop()

