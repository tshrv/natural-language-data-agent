from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg

from config import settings
from utils.logging import logger


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Context manager to acquire and automatically release a connection."""
    connection: asyncpg.Connection = await asyncpg.connect(settings.db_url)    
    logger.debug(f"Connected to database: {settings.postgres_db} at {settings.postgres_host}:{settings.postgres_port}")
    yield connection
    await connection.close()
    logger.debug(f"Connection to database {settings.postgres_db} closed.")


async def test_db():
    async with get_db_connection() as conn:
        values = await conn.fetch('SELECT count(*) FROM customer')
        logger.debug(f'Customer count: {values[0]["count"]}')
