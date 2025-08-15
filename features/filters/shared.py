from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.get_info import is_master_of_alliance
import asyncpg


class IsAllianceMaster(BaseFilter):
    """
    Проверка на мастера альянса
    """
    async def __call__(self,
                       event: Union[Message, CallbackQuery],
                       state: FSMContext,
                       pool: asyncpg.pool.Pool) -> bool:
        data = await state.get_data()
        alliance_id = data.get("alliance_id")
        if not alliance_id:
            return False
        user_id = event.from_user.id
        return await is_master_of_alliance(pool=pool,
                                           alliance_id=alliance_id,
                                           tg_id=user_id)
