from decimal import Decimal
from uuid import uuid4

import pytest

from app.exceptions import ValidationException
from app.models.producto import ProductoCreate
from app.services.producto import ProductoService


class TestLeerProducto:
    async def test_listar_productos_vacio(self, service: ProductoService):
        productos = await service.leer.listar()

        assert productos == []

    async def test_listar_productos_con_datos(
        self,
        service: ProductoService,
        producto_data: ProductoCreate,
    ):
        await service.crear.execute(producto_data)

        productos = await service.leer.listar()

        assert len(productos) == 1
        assert productos[0].nombre == producto_data.nombre

    async def test_listar_productos_con_paginacion(self, service: ProductoService):
        for i in range(5):
            data = ProductoCreate(
                nombre=f"Producto {i}",
                precio=Decimal("10.00"),
                stock=1,
            )
            await service.crear.execute(data)

        productos = await service.leer.listar(skip=0, limit=3)

        assert len(productos) == 3

    async def test_listar_productos_paginacion_invalida_skip_negativo(
        self,
        service: ProductoService,
    ):
        with pytest.raises(ValidationException) as exc:
            await service.leer.listar(skip=-1)

        assert "skip" in str(exc.value).lower()

    async def test_listar_productos_paginacion_invalida_limit_cero(
        self,
        service: ProductoService,
    ):
        with pytest.raises(ValidationException) as exc:
            await service.leer.listar(limit=0)

        assert "límite" in str(exc.value).lower()

    async def test_listar_productos_paginacion_invalida_limit_mayor_1000(
        self,
        service: ProductoService,
    ):
        with pytest.raises(ValidationException) as exc:
            await service.leer.listar(limit=1001)

        assert "límite" in str(exc.value).lower()

    async def test_obtener_producto_existente(
        self,
        service: ProductoService,
        producto_data: ProductoCreate,
    ):
        producto_creado = await service.crear.execute(producto_data)

        producto = await service.leer.obtener(producto_creado.id)

        assert producto is not None
        assert producto.id == producto_creado.id
        assert producto.nombre == producto_data.nombre

    async def test_obtener_producto_inexistente(self, service: ProductoService):
        producto = await service.leer.obtener(uuid4())

        assert producto is None

    async def test_buscar_por_nombre_existente(
        self,
        service: ProductoService,
        producto_data: ProductoCreate,
    ):
        await service.crear.execute(producto_data)

        producto = await service.leer.buscar_por_nombre(producto_data.nombre)

        assert producto is not None
        assert producto.nombre == producto_data.nombre

    async def test_bajo_stock(self, service: ProductoService):
        await service.crear.execute(
            ProductoCreate(nombre="Alto stock", precio=Decimal("10.00"), stock=100)
        )
        await service.crear.execute(
            ProductoCreate(nombre="Bajo stock", precio=Decimal("10.00"), stock=2)
        )

        productos = await service.leer.bajo_stock(umbral=10)

        assert len(productos) == 1
        assert productos[0].nombre == "Bajo stock"
