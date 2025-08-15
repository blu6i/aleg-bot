import asyncpg
from utils import log

async def create_alliance(pool: asyncpg.pool, name: str, tg_id: int):
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Получаем ID игрока по его Telegram ID
                player_id = await conn.fetchval("""
                    SELECT id FROM players WHERE tg_id = $1
                """, tg_id)

                # Если игрока нет — регистрируем
                if not player_id:
                    player_id = await conn.fetchval("""
                        INSERT INTO players (tg_id)
                        VALUES ($1)
                        RETURNING id
                    """, tg_id)

                # Создаём альянс
                await conn.execute("""
                    INSERT INTO alliances (name, master_id)
                    VALUES ($1, $2)
                """, name, player_id)
    except Exception as e:
        log.error(f"Ошибка при добавление гильдии {name}: {e}")
