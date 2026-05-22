from uuid import UUID

from app.repositories.producto_repository import ProductoRepository


class EliminarProducto:
    def __init__(self, repository: ProductoRepository):
        self.repository = repository

    async def execute(self, producto_id: UUID) -> bool:
        return await self.repository.delete(producto_id)
