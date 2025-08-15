from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State, default_state
import asyncpg
from database import add_info


class AddAlliance(StatesGroup):
    input_name = State()
    confirm_create_alliance = State()


router = Router()


@router.message(F.text,
                Command('add_alliance'))
async def cmd_add_alliance(msg: Message, state: FSMContext):
    await state.update_data(name=None)
    await state.update_data(user_id=msg.from_user.id)
    text = (f"Укажите название альянса")
    await msg.answer(text=text)
    await state.set_state(AddAlliance.input_name)


@router.message(F.text,
                AddAlliance.input_name)
async def input_name_alliance(msg: Message, state: FSMContext):
    name = msg.text
    await state.update_data(name=name)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать", callback_data="create_alliance")]
    ]
    )
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
    if data["user_id"] == call.from_user.id:
        name = data["name"]
        if not name:
            await call.message.answer("Вы не указали название альянса")
            return
        # Добавить обработчик добавления в БД альянса
        await add_info.create_alliance(name=name,
                                       tg_id=call.from_user.id,
                                       pool=pool)
        await call.message.answer(text=f"Альянс {name} успешно создан")
        await state.clear()
    await call.answer()
