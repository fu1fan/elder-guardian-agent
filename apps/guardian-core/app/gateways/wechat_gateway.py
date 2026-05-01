from __future__ import annotations

import logging

from guardian_shared.schemas import AlertRecord

logger = logging.getLogger(__name__)


class WechatGateway:
    def __init__(self, mock: bool = True) -> None:
        self.mock = mock

    async def notify_family(self, alert: AlertRecord) -> None:
        if self.mock:
            logger.warning("[MOCK WECHAT] %s priority=%s event=%s", alert.message, alert.priority, alert.event_id)
            return
        logger.info("Real WeChat integration not configured; fallback log: %s", alert.message)

