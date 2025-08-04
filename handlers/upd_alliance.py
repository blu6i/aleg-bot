from math import ceil

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State, default_state
import asyncpg
from database import upd_info, get_info

class UpdInfoAlliance(StatesGroup):
    upd_alliances_list = State()
    upd_alliances_menu = State()
    rename_alliance = State()


router = Router()

def build_alliance_keyboard(alliances: list[dict], page: int = 1, per_page: int = 5) -> InlineKeyboardMarkup:
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
                callback_data=f"upd_alliance_{alliance['id']}"
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


@router.message(Command("upd_alliance"))
async def upd_alliance(msg: Message, state: FSMContext, pool: asyncpg.pool, **kwargs) -> None:
    """
    Хэндлер для обновления данных альянса
    :param msg: сообщение пользователя
    :param state: состояние
    :param pool: пул подключения к бд
    :param kwargs: доп. данные
    :return: None
    """
    await state.set_state(UpdInfoAlliance.upd_alliances_list)
    await state.update_data(user_id=msg.from_user.id)
    # Вызов функции получения альянсов у юзера
    alliances = await get_info.get_alliances_by_master(pool, msg.from_user.id)
    if not alliances:
        await msg.answer("У вас нет альянсов.")
        return

    keyboard = build_alliance_keyboard(alliances)
    # Конструктор клавиатуры с альянсами
    text = f"Выберите альянс, который хотите отредактировать"
    await msg.answer(text=text,
                     reply_markup=keyboard)

@router.callback_query(F.data.startswith("page_"),
                       UpdInfoAlliance.upd_alliances_list)
async def paginate_alliances(call: CallbackQuery, state: FSMContext, pool: asyncpg.pool) -> None:
    """
    Перелистывание страниц
    :param call: кнопка
    :param state: состояние
    :param pool: пул подкллючения
    :return: None
    """
    data = await state.get_data()
    user_id = data.get("user_id")
    if call.from_user.id == user_id:
        # данные для клавиатуры
        page = int(call.data.removeprefix("page_"))
        alliances = await get_info.get_alliances_by_master(pool, user_id)

        keyboard = build_alliance_keyboard(alliances, page=page)

        await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()

def build_alliance_action_keyboard(alliance_id: int, has_chat: bool) -> InlineKeyboardMarkup:
    """
    Конструктор клавиатуры для настроек альянса
    :param alliance_id: ид альянса
    :param has_chat: привязан ли чат
    :return: инлайн клавиатура с настройками
    """
    keyboard = [
        [InlineKeyboardButton(text="✏️ Редактировать название", callback_data=f"edit_name_{alliance_id}")],
        [InlineKeyboardButton(text="🛠 Состав альянса", callback_data=f"edit_members_{alliance_id}")],
        [InlineKeyboardButton(text="🔁 Передать мастера", callback_data=f"transfer_master_{alliance_id}")],
        [InlineKeyboardButton(
            text="🚪 Отвязать чат" if has_chat else "🔗 Привязать чат",
            callback_data=f"{'unlink' if has_chat else 'link'}_chat_{alliance_id}"
        )],
        [InlineKeyboardButton(text="🗑 Удалить альянс", callback_data=f"delete_alliance_{alliance_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_alliances")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data.startswith("upd_alliance_"),
                       UpdInfoAlliance.upd_alliances_list)
async def show_alliance_actions(call: CallbackQuery, state: FSMContext, pool: asyncpg.Pool) -> None:
    """
    Вывод настроек альянса
    :param call: кнопка
    :param state: состояние
    :param pool: пул к бд
    :return: None
    """
    data = await state.get_data()
    alliance_id = int(call.data.split("_")[-1])
    user_id = call.from_user.id
    if user_id == data.get("user_id"):
        is_master = await get_info.is_master_of_alliance(pool, alliance_id, user_id)
        if is_master:
            alliance = await get_info.get_alliance_info(pool, alliance_id)
            if not alliance:
                return

            keyboard = build_alliance_action_keyboard(alliance_id, has_chat=bool(alliance["chat_id"]))
            await call.message.edit_text(
                f"Выберите действие для альянса «{alliance['name']}»:",
                reply_markup=keyboard
            )
            await state.set_state(UpdInfoAlliance.upd_alliances_menu)

    await call.answer()

@router.callback_query(F.data == "back_to_alliances",
                       UpdInfoAlliance.upd_alliances_menu)
async def back_to_alliances(call: CallbackQuery, state: FSMContext, pool: asyncpg.Pool):
    data = await state.get_data()
    user_id = data.get("user_id", call.from_user.id)
    if call.from_user.id == user_id:
        alliances = await get_info.get_alliances_by_master(pool, user_id)
        keyboard = build_alliance_keyboard(alliances, page=0)
        await call.message.edit_text("Выберите альянс для редактирования:", reply_markup=keyboard)
        await state.set_state(UpdInfoAlliance.upd_alliances_list)
    await call.answer()

@router.callback_query(F.data.startswith(("edit_name_", "edit_members_", "transfer_master_", "unlink_chat_", "link_chat_", "delete_alliance_")),
                       UpdInfoAlliance.upd_alliances_menu)
async def placeholder_handler(call: CallbackQuery):
    await call.answer("Функция в разработке", show_alert=True)
