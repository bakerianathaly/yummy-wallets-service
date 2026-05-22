from decimal import Decimal

import pytest

from app.exceptions import ProductoYaExisteException, ValidationException
from app.models.producto import ProductoCreate
from app.services.producto import ProductoService


class TestCrearProducto:
    async def test_crear_producto_exitoso(
        self,
        service: ProductoService,
        producto_data: ProductoCreate,
    ):
        producto = await service.crear.execute(producto_data)

        assert producto.nombre == producto_data.nombre
        assert producto.descripcion == producto_data.descripcion
        assert producto.precio == producto_data.precio
        assert producto.stock == producto_data.stock
        assert producto.id is not None

    async def test_crear_producto_duplicado(
        self,
        service: ProductoService,
        producto_data: ProductoCreate,
    ):
        await service.crear.execute(producto_data)

        with pytest.raises(ProductoYaExisteException):
            await service.crear.execute(producto_data)

    async def test_crear_producto_precio_negativo(self, service: ProductoService):
        data = ProductoCreate(
            nombre="Producto Test",
            precio=Decimal("-5.00"),
            stock=10,
        )

        with pytest.raises(ValidationException) as exc:
            await service.crear.execute(data)

        assert "precio" in str(exc.value).lower()

    async def test_crear_producto_precio_cero(self, service: ProductoService):
        data = ProductoCreate(
            nombre="Producto Test",
            precio=Decimal("0.00"),
            stock=10,
        )

        with pytest.raises(ValidationException) as exc:
            await service.crear.execute(data)

        assert "precio" in str(exc.value).lower()

    async def test_crear_producto_stock_negativo(self, service: ProductoService):
        data = ProductoCreate(
            nombre="Producto Test",
            precio=Decimal("100.00"),
            stock=-5,
        )

        with pytest.raises(ValidationException) as exc:
            await service.crear.execute(data)

        assert "stock" in str(exc.value).lower()

    async def test_crear_producto_stock_mayor_10000(self, service: ProductoService):
        data = ProductoCreate(
            nombre="Producto Test",
            precio=Decimal("100.00"),
            stock=10001,
        )

        with pytest.raises(ValidationException) as exc:
            await service.crear.execute(data)

        assert "stock" in str(exc.value).lower()

    async def test_crear_producto_nombre_menor_3_caracteres(
        self, service: ProductoService
    ):
        data = ProductoCreate(
            nombre="  AB  ",
            precio=Decimal("100.00"),
            stock=10,
        )

        with pytest.raises(ValidationException) as exc:
            await service.crear.execute(data)

        assert "nombre" in str(exc.value).lower()

    async def test_crear_producto_sin_descripcion(self, service: ProductoService):
        data = ProductoCreate(
            nombre="Producto Sin Desc",
            precio=Decimal("50.00"),
            stock=5,
        )

        producto = await service.crear.execute(data)

        assert producto.nombre == "Producto Sin Desc"
        assert producto.descripcion is None
