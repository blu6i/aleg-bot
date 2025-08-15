from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
import asyncpg
from aiogram.types import TelegramObject
from redis.asyncio import Redis


# class DBMiddleware(BaseMiddleware):
#     def __init__(self, pool: asyncpg.pool, redis: Redis):
#         self.pool = pool
#         self.redis = redis
#     async def __call__(
#         self,
#         handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
#         event: TelegramObject,
#         data: Dict[str, Any]
#     ) -> Any:
#         data["pool"] = self.pool
#         data["redis"] = self.redis
#         return await handler(event, data)
