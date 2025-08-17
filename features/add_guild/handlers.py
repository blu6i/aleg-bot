from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import asyncpg

from utils import log

from .states import AddGuildStates
from .keyboards import create_guild_keyboard
from .logic import process_create_guild

from database.guilds import get_guilds_user


router = Router()

@router.message(Command("create_guild"))
async def create_guild(msg: Message,
                       state: FSMContext):
    await state.clear()
    await state.set_state(AddGuildStates.first_input_name)
    text = "Введите название гильдии в новом сообщении:"
    await msg.answer(text=text)

@router.message(F.text,
                AddGuildStates.first_input_name)
async def first_input_name(msg: Message,
                           state: FSMContext):
    name = msg.text
    await state.update_data(name_guild=name)
    text = (f"Нажмите создать или введите другое название\n"
            f"\n"
            f"Название: {name}")
    keyboard = create_guild_keyboard()
    await msg.answer(text=text,
                     reply_markup=keyboard)


@router.callback_query(F.data == "confirm",
                       AddGuildStates.first_input_name)
async def create_new_guild(call: CallbackQuery,
                           state:FSMContext,
                           pool: asyncpg.Pool):
    data = await state.get_data()
    name = data.get("name_guild")
    user_id = call.from_user.id
    if not name:
        log.warning("Попытка подтвердить ввод названия гильдии без ввода имени")
        await state.clear()
        return
    await process_create_guild(pool=pool,
                               name=name,
                               user_id=user_id)
    await call.message.edit_text(f"Гильдия {name} успешно создана")
    await call.answer()

@router.message(Command("settings_guild"))
async def settings_guilds(msg: Message, pool: asyncpg.Pool):
    guilds = await get_guilds_user(pool=pool,
                                   tg_id=msg.from_user.id)
    text = ("Ваши гильдии:\n"
            "\n")
    for guild in guilds:
        text += f"\n{guild["name"]}"
    await msg.answer(text=text)

