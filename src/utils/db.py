from contextlib import asynccontextmanager

import asyncpg
from pydantic import BaseModel, ConfigDict

from config import settings
from utils.logging import logger


class DatabaseConnection(BaseModel):
    id: str
    connection: asyncpg.Connection
    model_config = ConfigDict(arbitrary_types_allowed=True)


class Database:
    POOL: asyncpg.Pool = None

    @classmethod
    async def connect(cls):
        """Create connections pool"""
        cls.POOL = await asyncpg.create_pool(settings.db_url, min_size=1, max_size=5)
        logger.debug("Database connections established successfully")

    @classmethod
    async def disconnect(cls):
        """Close all connections and clear pool"""
        if cls.POOL:
            await cls.POOL.close()
            logger.debug("Database connections closed successfully")

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        """Aquire connection from pool"""
        if cls.POOL is None:
            raise RuntimeError(
                "Database pool not initialized, call `Database.connect()` first"
            )
        async with cls.POOL.acquire() as connection:
            logger.debug("Database connection aquired")
            yield connection


async def test_db_connection():
    async with Database.get_connection() as conn:
        values = await conn.fetch("SELECT count(*) FROM customer")
        logger.debug(f"Customer count: {values[0]['count']}")
