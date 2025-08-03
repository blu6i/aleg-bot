from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State, default_state
import asyncpg
from database import upd_info

class UpdInfoAlliance(StatesGroup):
    menu_upd_alliance = State()
    rename_alliance = State()

router = Router()

@router.message(F.text,
                Command("upd_alliance"))
async def