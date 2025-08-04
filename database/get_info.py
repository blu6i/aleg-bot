import asyncpg

async def get_alliances_by_master(pool: asyncpg.pool, tg_id: int) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, name FROM alliances
            WHERE master_id = (SELECT id FROM players WHERE tg_id = $1)
        """, tg_id)

    return [dict(row) for row in rows]

async def get_player_id(pool: asyncpg.Pool, tg_id: int) -> int | None:
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT id FROM players WHERE tg_id = $1", tg_id)

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