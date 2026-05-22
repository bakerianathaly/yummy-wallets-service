from app.repositories.producto_repository import ProductoRepository
from app.services.producto.actualizar_producto import ActualizarProducto
from app.services.producto.crear_producto import CrearProducto
from app.services.producto.eliminar_producto import EliminarProducto
from app.services.producto.leer_producto import LeerProducto


class ProductoService:
    def __init__(self, repository: ProductoRepository):
        self.crear = CrearProducto(repository)
        self.leer = LeerProducto(repository)
        self.actualizar = ActualizarProducto(repository)
        self.eliminar = EliminarProducto(repository)
