from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.productos import router as productos_router
from shared.config import DESCRIPTION, PROJECT_NAME, VERSION

app = FastAPI(title=PROJECT_NAME, description=DESCRIPTION, version=VERSION)

app.include_router(health_router)
app.include_router(productos_router, prefix="/api/v1")


@app.get("/")
async def read_root():
    return {"message": "¡Proyecto FastAPI funcionando con Docker y Postgres!"}
