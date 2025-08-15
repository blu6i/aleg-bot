from math import ceil

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def confirm_keyboard(name_button: str = "Принять",
                     callback_name: str = "confirm") -> InlineKeyboardMarkup:
    """
    Создает кнопку для подтверждения чего-либо с кастомным названием
    :param callback_name: название callback_data
    :param name_button: название кнопки. По умолчанию "Принять"
    :return: кнопку
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name_button,
                              callback_data=callback_name)]
    ])

def cancel_keyboard(name_button: str = "Отмена",
                    callback_name: str = "cancel") -> InlineKeyboardMarkup:
    """
    Создается кнопку для возврата в главное меню
    :param callback_name: название callback_data
    :param name_button: название кнопки. По умолчанию "Отмена"
    :return: Возвращает клавиатуру с кнопкой "Назад"
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name_button,
                              callback_data=callback_name)]
    ])

def cancel_confirm_keyboard(name_button_cancel: str = "Отмена",
                          name_button_confirm: str = "Принять") -> InlineKeyboardMarkup:
    """
    Создает кнопки подтверждения и отмены
    :param name_button_cancel: название кнопки отмены. По умолчанию "Отмена"
    :param name_button_confirm: название кнопки принятия. По умолчанию "Окей"
    :return: Возвращает клавиатуру с кнопками "Назад" и "Вперед"
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name_button_confirm,
                              callback_data="confirm")],
        [InlineKeyboardButton(text=name_button_cancel,
                              callback_data="cancel")]
    ])

def action_keyboard(alliance_id: int, has_chat: bool) -> InlineKeyboardMarkup:
    """
    Клавиатура для действий с альянсами
    :param alliance_id: ид альянса
    :param has_chat: привязан ли чат
    :return:
    """
    keyboard = [
        [InlineKeyboardButton(text="✏️ Редактировать название", callback_data=f"rename_alliance")],
        # [InlineKeyboardButton(text="🛠 Состав альянса", callback_data=f"edit_members")],
        # [InlineKeyboardButton(text="🔁 Передать мастера", callback_data=f"transfer_master")],
        [InlineKeyboardButton(
            text="🚪 Отвязать чат" if has_chat else "🔗 Привязать чат",
            callback_data=f"{'unlink' if has_chat else 'link'}_chat"
        )],
        [InlineKeyboardButton(text="🗑 Удалить альянс", callback_data=f"delete_alliance")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_alliances")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def alliance_list_keyboard(alliances: list[dict],
                           page: int = 1,
                           per_page: int = 5) -> InlineKeyboardMarkup:
    """
    Строит клавиатуру для вывода списка альянсов. Если у пользователя количество выводимых альянсов >5,
    то вывод разбивается на страницы по 5 альянсов на каждый
    :param alliances: альянсы пользователя
    :param page: выводимая страница
    :param per_page: кол-во выводимых страниц
    :return: клавиатура с альянсами
    """
    # Вычисление выводимых кол-ва альянсы
    total = len(alliances)
    total_pages = ceil(total / per_page)
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    end = start + per_page
    current_slice = alliances[start:end]

    keyboard: list[list[InlineKeyboardButton]] = []

    # Кнопки альянсов
    for alliance in current_slice:
        keyboard.append([
            InlineKeyboardButton(
                text=alliance["name"],
                callback_data=f"settings_alliance_{alliance['id']}"
            )
        ])

    # Кнопки навигации
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"page_{page - 1}"
            )
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="▶️ Далее",
                callback_data=f"page_{page + 1}"
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)