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
    entering_rename = State()
    confirm_rename = State()
    edit_members = State()
    transfer_master = State()
    link_chat = State()
    unlink_chat = State()
    delete_alliance = State()


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
        [InlineKeyboardButton(text="✏️ Редактировать название", callback_data=f"rename_alliance_{alliance_id}")],
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
    alliance_id = int(call.data.removeprefix("upd_alliance_"))
    user_id = call.from_user.id
    if user_id == data.get("user_id"):
        is_master = await get_info.is_master_of_alliance(pool, alliance_id, user_id)
        if is_master:
            alliance = await get_info.get_alliance_info(pool, alliance_id)
            if not alliance:
                return
            await state.update_data(alliance_id=alliance_id)
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
    user_id = data.get("user_id")
    if call.from_user.id == user_id:
        alliances = await get_info.get_alliances_by_master(pool, user_id)
        keyboard = build_alliance_keyboard(alliances, page=0)
        await call.message.edit_text("Выберите альянс для редактирования:", reply_markup=keyboard)
        await state.set_state(UpdInfoAlliance.upd_alliances_list)
    await call.answer()


@router.callback_query(
    F.data.startswith(("edit_members_", "transfer_master_")),
    UpdInfoAlliance.upd_alliances_menu)
async def placeholder_handler(call: CallbackQuery):
    await call.answer("Функция в разработке", show_alert=True)


@router.callback_query(UpdInfoAlliance.upd_alliances_menu,
                       F.data.startswith("rename_alliance_"))
async def start_rename_alliance(call: CallbackQuery, state: FSMContext, pool: asyncpg.pool) -> None:
    data = await state.get_data()
    if data.get("user_id") == call.from_user.id:
        alliance_id = int(int(call.data.removeprefix("rename_alliance_")))
        is_master = await get_info.is_master_of_alliance(pool=pool,
                                                         alliance_id=alliance_id,
                                                         tg_id=call.from_user.id)
        if is_master:
            await state.set_state(UpdInfoAlliance.entering_rename)
            await state.update_data(alliance_id=alliance_id)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="cancel_alliance_rename")]
            ])
            await call.message.edit_text(text="Введите новое название альянса",
                                         reply_markup=keyboard)
    await call.answer()


@router.message(F.text,
                StateFilter(UpdInfoAlliance.entering_rename, UpdInfoAlliance.confirm_rename))
async def input_alliance_name(msg: Message, state: FSMContext) -> None:
    new_name = msg.text
    await state.update_data(new_name=new_name)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Принять", callback_data="confirm_alliance_rename"),
             InlineKeyboardButton(text="Отмена", callback_data="cancel_alliance_rename")]
        ]
    )
    await state.set_state(UpdInfoAlliance.confirm_rename)
    await msg.answer(text=f"Новое название альянса: {new_name}\n"
                          f"Подтвердите ввод или введите другое название",
                     reply_markup=keyboard)


@router.callback_query(F.data == "confirm_alliance_rename",
                       UpdInfoAlliance.confirm_rename)
async def confirm_alliance_rename(call: CallbackQuery, state: FSMContext, pool: asyncpg.pool) -> None:
    data = await state.get_data()
    if call.from_user.id == data["user_id"]:
        is_master = await get_info.is_master_of_alliance(pool=pool,
                                                         alliance_id=data["alliance_id"],
                                                         tg_id=call.from_user.id)
        if is_master:
            await upd_info.upd_alliance_name(pool, data["alliance_id"], data["new_name"])
            alliance_info = await get_info.get_alliance_info(pool=pool,
                                                             alliance_id=data["alliance_id"])
            keyboard = build_alliance_action_keyboard(alliance_id=data["alliance_id"],
                                                      has_chat=bool(alliance_info["chat_id"]))
            await call.message.edit_text(f"Название альянса обновлено на {data["new_name"]}",
                                         reply_markup=keyboard)
            await state.set_state(UpdInfoAlliance.upd_alliances_menu)
    await call.answer()


@router.callback_query(F.data == "cancel_alliance_rename",
                       StateFilter(UpdInfoAlliance.confirm_rename, UpdInfoAlliance.entering_rename))
async def cancel_alliance_rename(call: CallbackQuery, state: FSMContext, pool: asyncpg.pool) -> None:
    data = await state.get_data()
    if call.from_user.id == data["user_id"]:
        is_master = await get_info.is_master_of_alliance(pool=pool,
                                                         alliance_id=data["alliance_id"],
                                                         tg_id=call.from_user.id)
        if is_master:
            alliance_info = await get_info.get_alliance_info(pool=pool,
                                                             alliance_id=data["alliance_id"])
            keyboard = build_alliance_action_keyboard(alliance_id=data["alliance_id"],
                                                      has_chat=bool(alliance_info["chat_id"]))
            await call.message.edit_text(f"Переименование отменено.",
                                         reply_markup=keyboard)
            await state.set_state(UpdInfoAlliance.upd_alliances_menu)
    await call.answer()


@router.callback_query(F.data.startswith("delete_alliance_"))
async def start_delete_alliance(call: CallbackQuery, state: FSMContext, pool: asyncpg.pool):
    data = await state.get_data()
    if call.from_user.id == data.get("user_id"):
        alliance_id = int(call.data.removeprefix("delete_alliance_"))
        is_master = await get_info.is_master_of_alliance(pool=pool,
                                                   alliance_id=alliance_id,
                                                   tg_id=call.from_user.id)
        if is_master:
            await state.set_state(UpdInfoAlliance.delete_alliance)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="cancel_delete")]
            ])
            await call.message.edit_text("Вы уверены, что хотите удалить альянс?\n"
                                         "Введите точное имя альянса для подтверждения:",
                                         reply_markup=keyboard)
    await call.answer()

@router.callback_query(F.data == "cancel_delete",
                       UpdInfoAlliance.delete_alliance)
async def cancel_alliance_rename(call: CallbackQuery, state: FSMContext, pool: asyncpg.pool) -> None:
    data = await state.get_data()
    if call.from_user.id == data["user_id"]:
        is_master = await get_info.is_master_of_alliance(pool=pool,
                                                         alliance_id=data["alliance_id"],
                                                         tg_id=call.from_user.id)
        if is_master:
            alliance_info = await get_info.get_alliance_info(pool=pool,
                                                             alliance_id=data["alliance_id"])
            keyboard = build_alliance_action_keyboard(alliance_id=data["alliance_id"],
                                                      has_chat=bool(alliance_info["chat_id"]))
            await call.message.edit_text(f"Удаление отменено.",
                                         reply_markup=keyboard)
            await state.set_state(UpdInfoAlliance.upd_alliances_menu)
    await call.answer()

@router.message(F.text,
                UpdInfoAlliance.delete_alliance)
async def confirm_delete_alliance(msg: Message, state: FSMContext, pool: asyncpg.pool):
    data = await state.get_data()
    alliance_name = await get_info.get_alliance_name(pool, data["alliance_id"])
    is_master = await get_info.is_master_of_alliance(pool=pool,
                                                     alliance_id=data["alliance_id"],
                                                     tg_id=msg.from_user.id)
    if is_master:
        if msg.text.strip() == alliance_name:
            await upd_info.delete_alliance(pool, data["alliance_id"])
            text = "Альянс удалён."
            alliances = await get_info.get_alliances_by_master(pool, msg.from_user.id)
            if alliances:
                keyboard = build_alliance_keyboard(alliances)
                await msg.answer(text=text,
                                 reply_markup=keyboard)
                await state.set_state(UpdInfoAlliance.upd_alliances_list)
            else:
                await msg.answer(text=text)
                await state.clear()
        else:
            text = "Название не совпадает. Удаление отменено."
            alliance_info = await get_info.get_alliance_info(pool=pool,
                                                             alliance_id=data["alliance_id"])
            keyboard = build_alliance_action_keyboard(alliance_id=data["alliance_id"],
                                                      has_chat=bool(alliance_info["chat_id"]))
            await msg.answer(text=text,
                             reply_markup=keyboard)
            await state.set_state(UpdInfoAlliance.upd_alliances_menu)
