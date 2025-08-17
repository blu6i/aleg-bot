import asyncpg
from database import guilds
from utils import log

async def process_create_guild(pool: asyncpg.Pool,
                           name: str,
                           user_id: int) -> bool:
    try:
        await guilds.create_guild(pool=pool,
                                  name=name,
                                  tg_id=user_id)
        return True
    except Exception as e:
        log.error(f"Ошибка при создании новой гильдии: {e}")
        return False

