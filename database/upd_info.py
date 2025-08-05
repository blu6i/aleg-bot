import asyncpg


async def upd_alliance_name(pool: asyncpg.Pool, alliance_id: int, new_name: str):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE alliances SET name = $1 WHERE id = $2", new_name, alliance_id)
