import asyncpg
from aiogram.filters import BaseFilter
from typing import Union

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery


class TypeChat(BaseFilter):
    def __init__(self, type_chat: Union[list, str]):
        self.type_chat = type_chat
    async def __call__(self,
                       event: Union[Message, CallbackQuery],
                       state: FSMContext,
                       pool: asyncpg.pool.Pool) -> bool:
        if isinstance(self.type_chat, str):
            return self.type_chat == event.chat.type
        else:
            return event.chat.type in self.type_chat
