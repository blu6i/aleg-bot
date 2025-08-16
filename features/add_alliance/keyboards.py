from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_alliance_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать", callback_data="create_alliance")]
    ]
    )
    return keyboard