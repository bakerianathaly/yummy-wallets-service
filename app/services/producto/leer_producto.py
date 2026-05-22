from typing import Optional
from uuid import UUID

from app.exceptions import ValidationException
from app.models.producto import Producto
from app.repositories.producto_repository import ProductoRepository


class LeerProducto:
    def __init__(self, repository: ProductoRepository):
        self.repository = repository

    async def listar(self, skip: int = 0, limit: int = 100) -> list[Producto]:
        self._validar_paginacion(skip, limit)
        return await self.repository.get_all(skip, limit)

    async def obtener(self, producto_id: UUID) -> Optional[Producto]:
        return await self.repository.get_by_id(producto_id)

    async def buscar_por_nombre(self, nombre: str) -> Optional[Producto]:
        return await self.repository.get_by_nombre(nombre)

    async def bajo_stock(
        self, umbral: int = 10, skip: int = 0, limit: int = 100
    ) -> list[Producto]:
        self._validar_paginacion(skip, limit)
        return await self.repository.get_bajo_stock(umbral, skip, limit)

    def _validar_paginacion(self, skip: int, limit: int) -> None:
        if skip < 0:
            raise ValidationException("El parámetro skip no puede ser negativo")
        if limit < 1:
            raise ValidationException("El límite debe ser al menos 1")
        if limit > 1000:
            raise ValidationException("El límite no puede exceder 1000")
