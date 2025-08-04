import asyncpg
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database import get_info

router = Router()

@router.message(F.text,
                Command("my_alliance"))
async def show_all_alliance(msg: Message, pool: asyncpg.pool, **kwargs):
    tg_id = msg.from_user.id
    alliances = await get_info.get_alliances_by_master(pool, tg_id)

    if not alliances:
        await msg.answer("У тебя пока нет гильдий.")
        return

    text = "Твои гильдии:\n"
    for guild in alliances:
        text += f"- {guild['name']}\n"

    await msg.answer(text)