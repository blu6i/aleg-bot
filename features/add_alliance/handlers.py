import asyncpg
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from database import alliances
from keyboards import (create_alliance_keyboard)


class AddAlliance(StatesGroup):
    input_name = State()
    confirm_create_alliance = State()


router = Router()


@router.message(F.text,
                Command('add_alliance'))
async def cmd_add_alliance(msg: Message, state: FSMContext):
    await state.update_data(name=None)
    await state.update_data(user_id=msg.from_user.id)
    text = f"Укажите название альянса в новом сообщении"
    await msg.answer(text=text)
    await state.set_state(AddAlliance.input_name)


@router.message(F.text,
                AddAlliance.input_name)
async def input_name_alliance(msg: Message, state: FSMContext):
    name = msg.text
    await state.update_data(name=name)
    keyboard = create_alliance_keyboard()
    text = (f"Нажмите создать или введите другое название\n"
            f"\n"
            f"Название: {name}")
    await msg.answer(text=text,
                     reply_markup=keyboard)


@router.callback_query(F.data == "create_alliance",
                       AddAlliance.input_name)
async def create_alliance(call: CallbackQuery,
                          state: FSMContext,
                          pool: asyncpg.pool):
    data = await state.get_data()
    name = data["name"]
    if not name:
        await call.message.answer("Вы не указали название альянса")
        return
    # Добавить обработчик добавления в БД альянса
    await alliances.create_alliance(name=name,
                                   tg_id=call.from_user.id,
                                   pool=pool)
    await call.message.answer(text=f"Альянс {name} успешно создан")
    await state.clear()
    await call.answer()
