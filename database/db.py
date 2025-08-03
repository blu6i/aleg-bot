import asyncpg
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
from utils import log

async def connect_db() -> asyncpg.pool:
    return await asyncpg.create_pool(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        min_size=1,
        max_size=10,
        command_timeout=60
    )

async def postgres_version(pool):
    async with pool.acquire() as conn:
        version = await conn.fetchval("SELECT version();")
        log.info(f"PostgreSQL version: {version}")