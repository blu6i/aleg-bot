import asyncpg

async def get_player_alliances(pool: asyncpg.pool, tg_id: int):
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT g.id, g.name
            FROM players p
            LEFT JOIN alliances g ON g.master_id = p.id
            WHERE p.tg_id = $1
        """, tg_id)
        return rows