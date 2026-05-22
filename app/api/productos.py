from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import ProductoDeps
from app.exceptions import (
    ProductoNotFoundException,
    ProductoYaExisteException,
    ValidationException,
)
from app.models.api_response import APIResponse
from app.models.producto import ProductoCreate, ProductoResponse, ProductoUpdate
from app.services.producto import ProductoService

router = APIRouter(prefix="/productos", tags=["productos"])


@router.post(
    "/",
    response_model=APIResponse[ProductoResponse],
    status_code=status.HTTP_201_CREATED,
)
async def crear_producto(
    producto: ProductoCreate,
    service: ProductoService = Depends(ProductoDeps.get_service),
) -> APIResponse[ProductoResponse]:
    try:
        nuevo = await service.crear.execute(producto)
        return APIResponse(success=True, message="Producto creado", outcome=[nuevo])
    except ProductoYaExisteException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=APIResponse[ProductoResponse])
async def listar_productos(
    skip: int = 0,
    limit: int = 100,
    service: ProductoService = Depends(ProductoDeps.get_service),
) -> APIResponse[ProductoResponse]:
    try:
        productos = await service.leer.listar(skip, limit)
        return APIResponse(
            success=True,
            message="Lista de productos" if productos else "No hay productos registrados",
            outcome=productos,
        )
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/buscar", response_model=APIResponse[ProductoResponse])
async def buscar_producto(
    nombre: str,
    service: ProductoService = Depends(ProductoDeps.get_service),
) -> APIResponse[ProductoResponse]:
    producto = await service.leer.buscar_por_nombre(nombre)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return APIResponse(success=True, message="Producto encontrado", outcome=[producto])


@router.get("/bajo-stock", response_model=APIResponse[ProductoResponse])
async def productos_bajo_stock(
    umbral: int = 10,
    skip: int = 0,
    limit: int = 100,
    service: ProductoService = Depends(ProductoDeps.get_service),
) -> APIResponse[ProductoResponse]:
    try:
        productos = await service.leer.bajo_stock(umbral, skip, limit)
        return APIResponse(
            success=True,
            message=f"Productos con stock <= {umbral}",
            outcome=productos,
        )
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{producto_id}", response_model=APIResponse[ProductoResponse])
async def obtener_producto(
    producto_id: UUID,
    service: ProductoService = Depends(ProductoDeps.get_service),
) -> APIResponse[ProductoResponse]:
    producto = await service.leer.obtener(producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return APIResponse(success=True, message="Producto encontrado", outcome=[producto])


@router.put("/{producto_id}", response_model=APIResponse[ProductoResponse])
async def actualizar_producto(
    producto_id: UUID,
    data: ProductoUpdate,
    service: ProductoService = Depends(ProductoDeps.get_service),
) -> APIResponse[ProductoResponse]:
    try:
        producto = await service.actualizar.execute(producto_id, data)
        return APIResponse(
            success=True, message="Producto actualizado", outcome=[producto]
        )
    except ProductoNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{producto_id}", response_model=APIResponse[ProductoResponse])
async def eliminar_producto(
    producto_id: UUID,
    service: ProductoService = Depends(ProductoDeps.get_service),
) -> APIResponse[ProductoResponse]:
    eliminado = await service.eliminar.execute(producto_id)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return APIResponse(success=True, message="Producto eliminado", outcome=[])
