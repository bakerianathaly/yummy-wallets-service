from decimal import Decimal
from uuid import uuid4

from app.models.producto import ProductoCreate
from app.repositories.producto_repository import ProductoRepository


class TestProductoRepository:
    async def test_create_producto(
        self,
        repo: ProductoRepository,
        producto_data: ProductoCreate,
    ):
        producto = await repo.create(producto_data)

        assert producto.nombre == producto_data.nombre
        assert producto.descripcion == producto_data.descripcion
        assert producto.precio == producto_data.precio
        assert producto.stock == producto_data.stock
        assert producto.id is not None

    async def test_get_by_id_existente(
        self,
        repo: ProductoRepository,
        producto_data: ProductoCreate,
    ):
        producto_creado = await repo.create(producto_data)

        producto = await repo.get_by_id(producto_creado.id)

        assert producto is not None
        assert producto.id == producto_creado.id
        assert producto.nombre == producto_data.nombre

    async def test_get_by_id_inexistente(self, repo: ProductoRepository):
        producto = await repo.get_by_id(uuid4())

        assert producto is None

    async def test_get_by_nombre_existente(
        self,
        repo: ProductoRepository,
        producto_data: ProductoCreate,
    ):
        await repo.create(producto_data)

        producto = await repo.get_by_nombre(producto_data.nombre)

        assert producto is not None
        assert producto.nombre == producto_data.nombre

    async def test_get_by_nombre_inexistente(self, repo: ProductoRepository):
        producto = await repo.get_by_nombre("Nombre Inexistente")

        assert producto is None

    async def test_get_all_vacio(self, repo: ProductoRepository):
        productos = await repo.get_all()

        assert productos == []

    async def test_get_all_con_datos(
        self,
        repo: ProductoRepository,
        producto_data: ProductoCreate,
    ):
        await repo.create(producto_data)

        productos = await repo.get_all()

        assert len(productos) == 1
        assert productos[0].nombre == producto_data.nombre

    async def test_get_all_con_paginacion(self, repo: ProductoRepository):
        for i in range(5):
            data = ProductoCreate(
                nombre=f"Producto {i}",
                precio=Decimal("10.00"),
                stock=1,
            )
            await repo.create(data)

        productos = await repo.get_all(skip=0, limit=3)

        assert len(productos) == 3

    async def test_get_all_con_skip(self, repo: ProductoRepository):
        for i in range(5):
            data = ProductoCreate(
                nombre=f"Producto {i}",
                precio=Decimal("10.00"),
                stock=1,
            )
            await repo.create(data)

        productos = await repo.get_all(skip=2, limit=10)

        assert len(productos) == 3

    async def test_get_bajo_stock(self, repo: ProductoRepository):
        await repo.create(ProductoCreate(nombre="Con stock", precio=Decimal("10.00"), stock=50))
        await repo.create(ProductoCreate(nombre="Bajo stock", precio=Decimal("10.00"), stock=3))

        productos = await repo.get_bajo_stock(umbral=10)

        assert len(productos) == 1
        assert productos[0].nombre == "Bajo stock"

    async def test_update_producto(
        self,
        repo: ProductoRepository,
        producto_data: ProductoCreate,
    ):
        producto = await repo.create(producto_data)
        producto.nombre = "Nombre Actualizado"

        actualizado = await repo.update(producto)

        assert actualizado.nombre == "Nombre Actualizado"

    async def test_delete_existente(
        self,
        repo: ProductoRepository,
        producto_data: ProductoCreate,
    ):
        producto_creado = await repo.create(producto_data)

        resultado = await repo.delete(producto_creado.id)

        assert resultado is True

        producto = await repo.get_by_id(producto_creado.id)
        assert producto is None

    async def test_delete_inexistente(self, repo: ProductoRepository):
        resultado = await repo.delete(uuid4())

        assert resultado is False
