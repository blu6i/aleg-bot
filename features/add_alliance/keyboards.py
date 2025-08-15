from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def confirm_keyboard(name_button: str) -> InlineKeyboardMarkup:
    """
    Создает кнопку для подтверждения чего-либо с кастомным названием
    :param name_button: название кнопки
    :return: кнопку
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name_button,
                              callback_data="confirm")]
    ])
