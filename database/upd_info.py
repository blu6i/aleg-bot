import asyncpg


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