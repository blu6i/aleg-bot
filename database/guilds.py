import asyncpg

from utils import log


async def create_guild(pool: asyncpg.pool, name: str, tg_id: int):
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Получаем ID игрока по его Telegram ID
            player_id = await conn.fetchval("""
                SELECT id FROM players WHERE tg_id = $1
            """, tg_id)

            # Если игрока нет - регистрируем
            if not player_id:
                player_id = await conn.fetchval("""
                    INSERT INTO players (tg_id)
                    VALUES ($1)
                    RETURNING id
                """, tg_id)

            # Создаём гильдию
            await conn.execute("""
                INSERT INTO guilds (name, master_id)
                VALUES ($1, $2)
            """, name, player_id)


async def get_guilds_user(pool: asyncpg.Pool, tg_id: int) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, name FROM guilds
            WHERE master_id = (SELECT id FROM players WHERE tg_id = $1)
            ORDER BY name
        """, tg_id)
    return [dict(row) for row in rows]