from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import TypeVar


T = TypeVar("T")


class ElderSerialQueue:
    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def run(self, elder_id: str, fn: Callable[[], Awaitable[T]]) -> T:
        async with self._locks[elder_id]:
            return await fn()

