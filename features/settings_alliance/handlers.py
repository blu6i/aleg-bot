import asyncpg
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from redis.asyncio import Redis

from database import players
from features.filters.chat import TypeChat
from features.filters.shared import IsAllianceMaster
from features.filters.user import HaveRequestByUser
from utils import log
from .keyboards import (cancel_keyboard,
                        cancel_confirm_keyboard,
                        alliance_list_keyboard)
from .logic import (get_alliance_list,
                    get_action_menu,
                    create_bind_redis,
                    process_bind_chat,
                    process_unbind_chat, process_delete_alliance, process_alliance_rename)
from .states import UpdInfoAlliance

router = Router()


# Фикс
@router.message(Command("my_alliances"))
async def upd_alliance(msg: Message, state: FSMContext, pool: asyncpg.pool, **kwargs) -> None:
    """
    Вывод списка альянса
    :param msg: сообщение пользователя
    :param state: состояние
    :param pool: пул подключения к бд
    :param kwargs: доп. данные
    :return: None
    """
    await state.set_state(UpdInfoAlliance.upd_alliances_list)
    alliance_data = await get_alliance_list(pool=pool,
                                            user_id=msg.from_user.id)
    if alliance_data is None:
        text = ("У вас нет альянса.\n"
                "Введите /create_alliance, чтобы создать альянс.")
        await msg.answer(text=text,
                         parse_mode="HTML")
        return
    await msg.answer(text=alliance_data["text"],
                     reply_markup=alliance_data["keyboard"])


# Фикс
@router.callback_query(F.data.startswith("page_"),
                       UpdInfoAlliance.upd_alliances_list)
async def paginate_alliances(call: CallbackQuery,
                             state: FSMContext,
                             pool: asyncpg.pool) -> None:
    """
    Перелистывание страниц
    :param call: кнопка
    :param state: состояние
    :param pool: пул подкллючения
    :return: None
    """
    page = int(call.data.removeprefix("page_"))
    alliances = await players.get_alliances_by_master(pool, call.from_user.id)

    keyboard = alliance_list_keyboard(alliances, page=page)

    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()


# Фикс
@router.callback_query(F.data.startswith("settings_alliance_"),
                       UpdInfoAlliance.upd_alliances_list)
async def show_alliance_actions(call: CallbackQuery, state: FSMContext, pool: asyncpg.Pool) -> None:
    """
    Вывод настроек альянса
    :param call: кнопка
    :param state: состояние
    :param pool: пул к бд
    :return: None
    """
    alliance_id = int(call.data.removeprefix("settings_alliance_"))
    alliance_data = await get_action_menu(pool=pool,
                                          alliance_id=alliance_id)
    if not alliance_data:
        log.error(f"Ошибка создания клавиатуры для альянса {alliance_id}")
        return
    await state.update_data(alliance_id=alliance_id)
    await call.message.edit_text(
        text=alliance_data["text"],
        reply_markup=alliance_data["keyboard"]
    )
    await state.set_state(UpdInfoAlliance.upd_alliances_menu)
    await call.answer()


# =====[Смена названия альянса]===== -Фикс
@router.callback_query(UpdInfoAlliance.upd_alliances_menu,
                       F.data == "rename_alliance")
async def start_rename_alliance(call: CallbackQuery, state: FSMContext) -> None:
    """
    Начало переименования альянса
    :param call:
    :param state:
    :return:
    """
    keyboard = cancel_keyboard(name_button="Отменить")
    text = "Введите новое название альянса:"
    await state.set_state(UpdInfoAlliance.entering_rename)
    await call.message.edit_text(text=text,
                                 reply_markup=keyboard)
    await call.answer()


@router.message(F.text,
                StateFilter(UpdInfoAlliance.entering_rename, UpdInfoAlliance.confirm_rename))
async def input_alliance_name(msg: Message, state: FSMContext) -> None:
    """
    Обработка ввода нового названия альянса
    :param msg:
    :param state:
    :return:
    """
    new_name = msg.text
    await state.update_data(new_name=new_name)
    keyboard = cancel_confirm_keyboard(name_button_cancel="Отменить",
                                       name_button_confirm="Изменить")
    text = (f"Новое название альянса: {new_name}\n"
            f"Подтвердите ввод или введите другое название")
    await state.set_state(UpdInfoAlliance.confirm_rename)
    await msg.answer(text=text,
                     reply_markup=keyboard)


@router.callback_query(F.data == "confirm",
                       UpdInfoAlliance.confirm_rename,
                       IsAllianceMaster())
async def confirm_alliance_rename(call: CallbackQuery, state: FSMContext, pool: asyncpg.pool) -> None:
    """
    Принятие нового названия
    :param call:
    :param state:
    :param pool:
    :return:
    """
    data = await state.get_data()

    result = await process_alliance_rename(
        alliance_id=data["alliance_id"],
        new_name=data.get("new_name"),
        pool=pool
    )

    if result["success"]:
        await call.message.edit_text(
            text=result["text"],
            reply_markup=result["keyboard"]
        )
        await state.set_state(UpdInfoAlliance.upd_alliances_menu)
    else:
        log.error(result["error"])
    await call.answer()


@router.callback_query(F.data == "cancel",
                       StateFilter(UpdInfoAlliance.confirm_rename, UpdInfoAlliance.entering_rename))
async def cancel_alliance_rename(call: CallbackQuery, state: FSMContext, pool: asyncpg.pool) -> None:
    """
    Отмена переименования названия
    :param call:
    :param state:
    :param pool:
    :return:
    """
    data = await state.get_data()
    alliance_id = data["alliance_id"]
    text = "Переименование отменено"
    msg_keyboard_data = await get_action_menu(pool=pool,
                                              alliance_id=alliance_id,
                                              custom_text=text)
    await call.message.edit_text(text=msg_keyboard_data["text"],
                                 reply_markup=msg_keyboard_data["keyboard"])

    await state.set_state(UpdInfoAlliance.upd_alliances_menu)
    await call.answer()


# =====[Удаление альянса]=====
@router.callback_query(F.data.startswith("delete_alliance"),
                       IsAllianceMaster())
async def start_delete_alliance(call: CallbackQuery, state: FSMContext):
    """
    Запуск процесса удаления альянса
    :param call:
    :param state:
    :return:
    """
    await state.set_state(UpdInfoAlliance.delete_alliance)
    text = ("Вы уверены, что хотите удалить альянс?\n"
            "Введите точное имя альянса для подтверждения:")
    keyboard = cancel_keyboard(name_button="Назад")
    await call.message.edit_text(text=text,
                                 reply_markup=keyboard)
    await call.answer()


@router.callback_query(F.data == "cancel",
                       UpdInfoAlliance.delete_alliance)
async def cancel_alliance_rename(call: CallbackQuery, state: FSMContext, pool: asyncpg.pool) -> None:
    """
    Отмена удаления альянса
    :param call:
    :param state:
    :param pool:
    :return:
    """
    data = await state.get_data()
    alliance_id = data["alliance_id"]
    text = "Удаление отменено"
    msg_keyboard_data = await get_action_menu(pool=pool,
                                              alliance_id=alliance_id,
                                              custom_text=text)
    await call.message.edit_text(text=msg_keyboard_data["text"],
                                 reply_markup=msg_keyboard_data["keyboard"])

    await state.set_state(UpdInfoAlliance.upd_alliances_menu)
    await call.answer()


@router.message(F.text,
                UpdInfoAlliance.delete_alliance,
                IsAllianceMaster())
async def confirm_delete_alliance(msg: Message, state: FSMContext, pool: asyncpg.pool):
    """
    Подтверждение удаления альянса
    :param msg:
    :param state:
    :param pool:
    :return:
    """
    data = await state.get_data()
    result = await process_delete_alliance(
        user_id=msg.from_user.id,
        alliance_id=data["alliance_id"],
        entered_name=msg.text.strip(),
        pool=pool
    )

    await msg.answer(
        text=result["text"],
        reply_markup=result.get("keyboard")
    )

    # Установка состояния в зависимости от результата
    if result["success"]:
        if result.get("has_other_alliances"):
            await state.set_state(UpdInfoAlliance.upd_alliances_list)
        else:
            await state.clear()
    else:
        await state.set_state(UpdInfoAlliance.upd_alliances_menu)


# =====[Привязка чата]=====
@router.callback_query(F.data.startswith("link_chat"),
                       UpdInfoAlliance.upd_alliances_menu,
                       IsAllianceMaster())
async def start_bind_chat(call: CallbackQuery,
                          state: FSMContext,
                          redis: Redis):
    """
    Начало привязки чата к альянсу
    :param call:
    :param state:
    :param redis:
    :return:
    """
    data = await state.get_data()
    alliance_id = data.get("alliance_id")
    user_id = call.from_user.id

    await create_bind_redis(redis=redis,
                            alliance_id=alliance_id,
                            user_id=user_id)
    text = ("*Чтобы привязать чат*, отправьте следующую команду в нужном групповом чате:\n"
            "\n"
            "`/confirm_chat`\n"
            "\n"
            "_Время действия: 5 минут._")
    await call.message.edit_text(text=text)


@router.message(Command("confirm_chat"),
                TypeChat(["group", "supergroup"]),
                HaveRequestByUser("guild_transfer"))
async def confirm_chat_link(msg: Message,
                            state: FSMContext,
                            pool: asyncpg.pool,
                            redis: Redis):
    """
    Подтверждение привязки чата к альянсу
    :param msg:
    :param state:
    :param pool:
    :param redis:
    :return:
    """
    result = await process_bind_chat(user_id=msg.from_user.id, chat_id=msg.chat.id, pool=pool, redis=redis)
    if isinstance(result, str):
        await msg.answer(f"❌ {result}")
    elif result:
        await msg.answer("✅ Чат успешно привязан к альянсу.")
    else:
        await msg.answer(f"❌ Проблема с привязкой чата")


@router.callback_query(F.data.startswith("unlink_chat"),
                       UpdInfoAlliance.upd_alliances_menu,
                       IsAllianceMaster())
async def unbind_chat(call: CallbackQuery, state: FSMContext, pool: asyncpg.pool):
    """
    Отвязка чата от альянса
    :param call:
    :param state:
    :param pool:
    :return:
    """
    data = await state.get_data()
    alliance_id = data.get("alliance_id")

    result = await process_unbind_chat(user_id=call.from_user.id, alliance_id=alliance_id, pool=pool)

    if result:
        text = "🔄 Чат успешно отвязан от альянса."
        keyboard_msg_data = await get_action_menu(pool=pool, alliance_id=alliance_id, custom_text=text)
        await call.message.edit_text(text=keyboard_msg_data["text"],
                                     reply_markup=keyboard_msg_data["keyboard"])
    else:
        await call.answer()
        return


@router.callback_query(F.data == "back_to_alliances",
                       UpdInfoAlliance.upd_alliances_menu)
async def back_to_alliances(call: CallbackQuery, state: FSMContext, pool: asyncpg.Pool):
    """
    Возврат в меню выбора альянса
    :param call:
    :param state:
    :param pool:
    :return:
    """
    alliance_data = await get_alliance_list(pool=pool,
                                            user_id=call.from_user.id)
    if alliance_data is None:
        await call.message.edit_text(text="У вас нет альянса.\n"
                                          "Введите /create_alliance, чтобы создать альянс.",
                                     parse_mode="HTML")
        return

    await call.message.edit_text(text=alliance_data["text"],
                                 reply_markup=alliance_data["keyboard"])
    await state.set_state(UpdInfoAlliance.upd_alliances_list)
    await call.answer()


# @router.callback_query(
#     F.data.startswith(("edit_members_", "transfer_master_")),
#     UpdInfoAlliance.upd_alliances_menu)
# async def placeholder_handler(call: CallbackQuery):
#     """
#     Заглушка
#     :param call:
#     :return:
#     """
#     await call.answer("Функция в разработке", show_alert=True)
