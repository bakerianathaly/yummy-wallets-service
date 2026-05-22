import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")

if "sqlite" in DATABASE_URL:
    async_engine = create_async_engine(DATABASE_URL, echo=False)
else:
    async_url = str(DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://")
    async_engine = create_async_engine(async_url, pool_pre_ping=True)

async_session_factory = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with async_session_factory() as session:
        yield session
