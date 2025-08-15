import asyncpg
from aiogram.filters import BaseFilter
from typing import Union

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from redis.asyncio import Redis

class HaveRequestByUser(BaseFilter):
    def __init__(self,
                 prefix: str):
        self.prefix = prefix
    async def __call__(self,
                        event: Union[Message, CallbackQuery],
                        state: FSMContext,
                        redis: Redis):
        key = f"{self.prefix}:{event.from_user.id}"
        return await redis.exists(key)