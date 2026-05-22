from decimal import Decimal

from app.exceptions import ProductoYaExisteException, ValidationException
from app.models.producto import Producto, ProductoCreate
from app.repositories.producto_repository import ProductoRepository


class CrearProducto:
    MIN_STOCK = 0
    MAX_STOCK = 10000
    MIN_PRECIO = Decimal("0.01")

    def __init__(self, repository: ProductoRepository):
        self.repository = repository

    async def execute(self, producto_data: ProductoCreate) -> Producto:
        self._validar(producto_data)
        existente = await self.repository.get_by_nombre(producto_data.nombre)
        if existente:
            raise ProductoYaExisteException(
                f"Ya existe un producto con el nombre '{producto_data.nombre}'"
            )
        return await self.repository.create(producto_data)

    def _validar(self, producto_data: ProductoCreate) -> None:
        if producto_data.precio < self.MIN_PRECIO:
            raise ValidationException(
                f"El precio debe ser mayor o igual a {self.MIN_PRECIO}"
            )

        if producto_data.stock < self.MIN_STOCK:
            raise ValidationException("El stock no puede ser negativo")

        if producto_data.stock > self.MAX_STOCK:
            raise ValidationException(f"El stock no puede exceder {self.MAX_STOCK}")

        if producto_data.nombre and len(producto_data.nombre.strip()) < 3:
            raise ValidationException("El nombre debe tener al menos 3 caracteres")
