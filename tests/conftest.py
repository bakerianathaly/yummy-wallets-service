import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.models.user import UserCreate
from app.repositories.user_repository import UserRepository
from app.services.user import UserService


@pytest.fixture(name="db_session")
async def db_session_fixture():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(name="repo")
def repo_fixture(db_session: AsyncSession) -> UserRepository:
    return UserRepository(db_session)


@pytest.fixture(name="service")
def service_fixture(repo: UserRepository) -> UserService:
    return UserService(repo)


@pytest.fixture(name="user_data")
def user_data_fixture() -> UserCreate:
    return UserCreate(
        email="test@yummy.com",
        full_name="Test User",
        password="Password123",
    )


@pytest.fixture(name="user_data_2")
def user_data_2_fixture() -> UserCreate:
    return UserCreate(
        email="other@yummy.com",
        full_name="Other User",
        password="Password456",
    )
