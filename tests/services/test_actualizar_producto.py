from decimal import Decimal
from uuid import uuid4

import pytest

from app.exceptions import ProductoNotFoundException, ValidationException
from app.models.producto import ProductoCreate, ProductoUpdate
from app.services.producto import ProductoService


class TestActualizarProducto:
    async def test_actualizar_nombre(
        self,
        service: ProductoService,
        producto_data: ProductoCreate,
    ):
        producto_creado = await service.crear.execute(producto_data)

        actualizado = await service.actualizar.execute(
            producto_creado.id,
            ProductoUpdate(nombre="Nombre Nuevo"),
        )

        assert actualizado.nombre == "Nombre Nuevo"
        assert actualizado.precio == producto_creado.precio

    async def test_actualizar_precio(
        self,
        service: ProductoService,
        producto_data: ProductoCreate,
    ):
        producto_creado = await service.crear.execute(producto_data)

        actualizado = await service.actualizar.execute(
            producto_creado.id,
            ProductoUpdate(precio=Decimal("250.00")),
        )

        assert actualizado.precio == Decimal("250.00")
        assert actualizado.nombre == producto_creado.nombre

    async def test_actualizar_stock(
        self,
        service: ProductoService,
        producto_data: ProductoCreate,
    ):
        producto_creado = await service.crear.execute(producto_data)

        actualizado = await service.actualizar.execute(
            producto_creado.id,
            ProductoUpdate(stock=50),
        )

        assert actualizado.stock == 50

    async def test_actualizar_producto_inexistente(self, service: ProductoService):
        with pytest.raises(ProductoNotFoundException):
            await service.actualizar.execute(
                uuid4(),
                ProductoUpdate(nombre="Nuevo Nombre"),
            )

    async def test_actualizar_precio_negativo(
        self,
        service: ProductoService,
        producto_data: ProductoCreate,
    ):
        producto_creado = await service.crear.execute(producto_data)

        with pytest.raises(ValidationException) as exc:
            await service.actualizar.execute(
                producto_creado.id,
                ProductoUpdate(precio=Decimal("-10.00")),
            )

        assert "precio" in str(exc.value).lower()

    async def test_actualizar_stock_negativo(
        self,
        service: ProductoService,
        producto_data: ProductoCreate,
    ):
        producto_creado = await service.crear.execute(producto_data)

        with pytest.raises(ValidationException) as exc:
            await service.actualizar.execute(
                producto_creado.id,
                ProductoUpdate(stock=-5),
            )

        assert "stock" in str(exc.value).lower()

    async def test_actualizar_nombre_corto(
        self,
        service: ProductoService,
        producto_data: ProductoCreate,
    ):
        producto_creado = await service.crear.execute(producto_data)

        with pytest.raises(ValidationException) as exc:
            await service.actualizar.execute(
                producto_creado.id,
                ProductoUpdate(nombre="AB"),
            )

        assert "nombre" in str(exc.value).lower()
