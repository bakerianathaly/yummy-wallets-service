from uuid import uuid4

from app.models.producto import ProductoCreate
from app.services.producto import ProductoService


class TestEliminarProducto:
    async def test_eliminar_producto_existente(
        self,
        service: ProductoService,
        producto_data: ProductoCreate,
    ):
        producto_creado = await service.crear.execute(producto_data)

        resultado = await service.eliminar.execute(producto_creado.id)

        assert resultado is True

        producto = await service.leer.obtener(producto_creado.id)
        assert producto is None

    async def test_eliminar_producto_inexistente(self, service: ProductoService):
        resultado = await service.eliminar.execute(uuid4())

        assert resultado is False
