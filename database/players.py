import asyncpg


async def get_player_id(pool: asyncpg.Pool, tg_id: int) -> int | None:
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT id FROM players WHERE tg_id = $1", tg_id)