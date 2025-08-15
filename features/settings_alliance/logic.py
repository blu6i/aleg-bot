import json

import asyncpg
from redis.asyncio import Redis

from database import get_info, upd_info
from utils import log
from .keyboards import alliance_list_keyboard, action_keyboard


async def get_alliance_list(pool: asyncpg.pool,
                            user_id: int,
                            custom_text: str = "") -> dict | None:
    """
    Создает меню со списком альянса с кастомным текстом в сообщении
    :param pool:
    :param user_id:
    :param custom_text:
    :return:
    """
    alliances = await get_info.get_alliances_by_master(pool=pool,
                                                       tg_id=user_id)
    if not alliances:
        return None

    return {
        "text": (f"Выберите альянс, который нужно отредактировать\n"
                 f"\n"
                 f"{custom_text}"),
        "keyboard": alliance_list_keyboard(alliances)
    }


async def get_action_menu(pool: asyncpg.pool.Pool,
                          alliance_id: int,
                          custom_text: str = "") -> dict | None:
    """
    Создает меню для редактирования альянса: смена названия, редактирование тг чата, удаление альянса
    :param pool:
    :param alliance_id:
    :param custom_text:
    :return:
    """
    alliance_info = await get_info.get_alliance_info(pool=pool,
                                                     alliance_id=alliance_id)
    if not alliance_info:
        return None

    text = (f"{custom_text}\n"
            f"Выберите действие для альянса «{alliance_info["name"]}»:")
    return {
        "text": text,
        "keyboard": action_keyboard(alliance_id=alliance_id,
                                    has_chat=bool(alliance_info["chat_id"]))
    }


async def rename_alliance(pool: asyncpg.pool.Pool,
                          alliance_id: int,
                          new_name: str) -> None:
    """
    Запуск процесса редактирования названия альянса
    :param pool:
    :param alliance_id:
    :param new_name:
    :return:
    """
    await upd_info.upd_alliance_name(pool=pool,
                                     alliance_id=alliance_id,
                                     new_name=new_name)


async def process_alliance_rename(alliance_id: int, new_name: str | None, pool: asyncpg.pool) -> dict:
    """
    Процесс редактирования ника. После ввода нового названия альянса - идет обработка и после чего добавляется в БД.
    :param alliance_id:
    :param new_name:
    :param pool:
    :return:
    """
    if not new_name:
        return {
            "success": False,
            "error": f"Ошибка при сохранении названия альянса {alliance_id}: не указано новое название"
        }

    await rename_alliance(pool=pool, alliance_id=alliance_id, new_name=new_name)

    msg_keyboard_data = await get_action_menu(
        pool=pool,
        alliance_id=alliance_id,
        custom_text=f"Название альянса обновлено на {new_name}"
    )

    if not msg_keyboard_data:
        return {
            "success": False,
            "error": f"Ошибка при построении клавиатуры меню после смены названия альянса {alliance_id}"
        }

    return {
        "success": True,
        "text": msg_keyboard_data["text"],
        "keyboard": msg_keyboard_data["keyboard"],
        "error": None
    }



async def create_bind_redis(redis: Redis,
                    alliance_id: int,
                    user_id: int) -> None:
    """
    Создает запись в редис для привязки чата к альянсу
    :param redis:
    :param alliance_id:
    :param user_id:
    :return:
    """
    key = f"guild_transfer:{int(user_id)}"
    value = json.dumps({
        "user_id": int(user_id),
        "alliance_id": int(alliance_id)
    })
    await redis.setex(key, 300, value)  # TTL 5 минут


async def process_bind_chat(user_id: int, chat_id: int, pool: asyncpg.pool, redis: Redis) -> str | bool:
    """
    Процесс привязки чата к гильдии
    1) Пользователь вводи команду в чате
    2) Если запись в реддис есть на добавление, то добавляет ид чат
    3) Если записи нет, то игнор (На верхнем уровне)
    :param user_id:
    :param chat_id:
    :param pool:
    :param redis:
    :return:
    """
    redis_key = f"guild_transfer:{user_id}"
    data = await redis.get(redis_key)
    if not data:
        return "Нет данных для привязки."

    try:
        binding_data = json.loads(data)
        alliance_id = int(binding_data["alliance_id"])
    except (KeyError, ValueError, json.JSONDecodeError):
        log.error(f"Ошибка: повреждённые данные в записи (guild_transfer:{user_id})")
        return False


    if not await get_info.is_master_of_alliance(pool, tg_id=user_id, alliance_id=alliance_id):
        log.warning(f"Попытка привязать не свой альянс. tg_id: {user_id} || alliance_id: {alliance_id}")
        return False

    alliance_data = await get_info.get_alliance_info(pool, alliance_id)
    if alliance_data["chat_id"]:
        log.warning(f"Попытка привязать чат к альянсу, у которого он уже привязан. tg_id: {user_id} || alliance_id: {alliance_id}")
        return "У альянса уже привязан чат."

    await upd_info.bind_chat_to_alliance(pool, alliance_id, chat_id)
    await redis.delete(redis_key)
    return True


async def process_unbind_chat(user_id: int, alliance_id: int, pool: asyncpg.pool) -> bool | str:
    """
    Процесс отвязки чата
    :param user_id:
    :param alliance_id:
    :param pool:
    :return:
    """
    if not await get_info.is_master_of_alliance(pool, tg_id=user_id, alliance_id=alliance_id):
        log.warning(f"Попытка отвязать чата не от своего альянса. tg_id: {user_id}, alliance_id: {alliance_id}")
        return False

    alliance_data = await get_info.get_alliance_info(pool, alliance_id)
    if not alliance_data["chat_id"]:
        log.warning(f"Попытка отвязать не привязанный чат к альянсу. tg_id: {user_id}, alliance_id: {alliance_id}")
        return False

    await upd_info.bind_chat_to_alliance(pool, alliance_id, None)
    return True


async def process_delete_alliance(user_id: int, alliance_id: int, entered_name: str, pool: asyncpg.pool) -> dict:
    """
    Процесс удаления альянса
    Возвращает словарь:
    {
        "success": bool,
        "text": str,
        "keyboard": InlineKeyboardMarkup | None,
        "has_other_alliances": bool
    }
    """
    alliance_name = await get_info.get_alliance_name(pool, alliance_id)

    if entered_name != alliance_name:
        alliance_info = await get_info.get_alliance_info(pool=pool, alliance_id=alliance_id)
        return {
            "success": False,
            "text": "Название не совпадает. Удаление отменено.",
            "keyboard": action_keyboard(
                alliance_id=alliance_id,
                has_chat=bool(alliance_info["chat_id"])
            )
        }

    await upd_info.delete_alliance(pool, alliance_id)

    alliances = await get_info.get_alliances_by_master(pool, user_id)
    return {
        "success": True,
        "text": "Альянс удалён.",
        "keyboard": alliance_list_keyboard(alliances) if alliances else None,
        "has_other_alliances": bool(alliances)
    }

