import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from . import models

load_dotenv()

PG_USER = os.getenv("DOCKER_PG_USER")
PG_PASSWORD = os.getenv("DOCKER_PG_PASSWORD")
PG_DB = os.getenv("DOCKER_PG_DB")
PG_URI = os.getenv("DOCKER_PG_URI")

DB_URL = f"postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}@{PG_URI}/{PG_DB}"

engine = create_async_engine(DB_URL)

SessionLocal = async_sessionmaker(bind=engine, autocommit=False, autoflush=False)


async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        await session.close()