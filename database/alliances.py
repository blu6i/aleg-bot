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


async def get_alliances_by_master(pool: asyncpg.pool, tg_id: int) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, name FROM alliances
            WHERE master_id = (SELECT id FROM players WHERE tg_id = $1)
            ORDER BY name
        """, tg_id)

    return [dict(row) for row in rows]


async def is_master_of_alliance(pool: asyncpg.Pool, alliance_id: int, tg_id: int) -> bool:
    async with pool.acquire() as conn:
        return await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM alliances
                WHERE id = $1 AND master_id = (SELECT id FROM players WHERE tg_id = $2)
            )
        """, alliance_id, tg_id)


async def get_alliance_info(pool: asyncpg.Pool, alliance_id: int) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, name, chat_id FROM alliances WHERE id = $1", alliance_id)
        return dict(row) if row else None


async def get_alliance_name(pool: asyncpg.Pool, alliance_id: int) -> str:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT name FROM alliances WHERE id = $1", alliance_id)
        return row["name"] if row else None


async def upd_alliance_name(pool: asyncpg.Pool, alliance_id: int, new_name: str):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE alliances SET name = $1 WHERE id = $2", new_name, alliance_id)


async def delete_alliance(pool: asyncpg.Pool, alliance_id: int):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM alliances WHERE id = $1", alliance_id)


async def bind_chat_to_alliance(pool: asyncpg.pool, alliance_id: int, chat_id: int | None):
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE alliances
            SET chat_id = $1
            WHERE id = $2
        """, chat_id, alliance_id)