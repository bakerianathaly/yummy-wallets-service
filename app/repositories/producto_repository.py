from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.producto import Producto, ProductoCreate


class ProductoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, producto_data: ProductoCreate) -> Producto:
        producto = Producto(**producto_data.model_dump())
        self.db.add(producto)
        await self.db.commit()
        await self.db.refresh(producto)
        return producto

    async def get_by_id(self, producto_id: UUID) -> Optional[Producto]:
        return await self.db.get(Producto, producto_id)

    async def get_by_nombre(self, nombre: str) -> Optional[Producto]:
        result = await self.db.execute(
            select(Producto).where(Producto.nombre.ilike(nombre))
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Producto]:
        result = await self.db.execute(select(Producto).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_total(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Producto))
        return result.scalar_one()

    async def get_bajo_stock(
        self, umbral: int = 10, skip: int = 0, limit: int = 100
    ) -> list[Producto]:
        result = await self.db.execute(
            select(Producto)
            .where(Producto.stock <= umbral)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, producto: Producto) -> Producto:
        self.db.add(producto)
        await self.db.commit()
        await self.db.refresh(producto)
        return producto

    async def delete(self, producto_id: UUID) -> bool:
        producto = await self.get_by_id(producto_id)
        if not producto:
            return False
        await self.db.delete(producto)
        await self.db.commit()
        return True
