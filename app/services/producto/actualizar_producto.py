from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.exceptions import ProductoNotFoundException, ValidationException
from app.models.producto import Producto, ProductoUpdate
from app.repositories.producto_repository import ProductoRepository


class ActualizarProducto:
    MIN_STOCK = 0
    MAX_STOCK = 10000
    MIN_PRECIO = Decimal("0.01")

    def __init__(self, repository: ProductoRepository):
        self.repository = repository

    async def execute(self, producto_id: UUID, data: ProductoUpdate) -> Producto:
        producto = await self.repository.get_by_id(producto_id)
        if not producto:
            raise ProductoNotFoundException(
                f"Producto con id {producto_id} no encontrado"
            )

        campos = data.model_dump(exclude_unset=True)
        self._validar(campos)

        for campo, valor in campos.items():
            setattr(producto, campo, valor)
        producto.updated_at = datetime.now()

        return await self.repository.update(producto)

    def _validar(self, campos: dict) -> None:
        precio = campos.get("precio")
        if precio is not None and precio < self.MIN_PRECIO:
            raise ValidationException(
                f"El precio debe ser mayor o igual a {self.MIN_PRECIO}"
            )

        stock = campos.get("stock")
        if stock is not None:
            if stock < self.MIN_STOCK:
                raise ValidationException("El stock no puede ser negativo")
            if stock > self.MAX_STOCK:
                raise ValidationException(f"El stock no puede exceder {self.MAX_STOCK}")

        nombre = campos.get("nombre")
        if nombre is not None and len(nombre.strip()) < 3:
            raise ValidationException("El nombre debe tener al menos 3 caracteres")
