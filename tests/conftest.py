import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.models.producto import ProductoCreate
from app.repositories.producto_repository import ProductoRepository
from app.services.producto import ProductoService


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
def repo_fixture(db_session: AsyncSession):
    return ProductoRepository(db_session)


@pytest.fixture(name="service")
def service_fixture(repo: ProductoRepository):
    return ProductoService(repo)


@pytest.fixture(name="producto_data")
def producto_data_fixture():
    return ProductoCreate(
        nombre="Producto Test",
        descripcion="Descripción de prueba",
        precio=100.50,
        stock=10,
    )
