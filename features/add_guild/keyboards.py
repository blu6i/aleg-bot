from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_guild_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать", callback_data="confirm")]
    ]
    )
    return keyboard