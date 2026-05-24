from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.users import router as users_router
from app.api.wallets import router as wallets_router
from app.exceptions import (
    DatabaseException,
    InactiveUserException,
    InactiveWalletException,
    InsufficientFundsException,
    InvalidTokenException,
    SameWalletTransferException,
)
from shared.config import API_PREFIX, DESCRIPTION, PROJECT_NAME, VERSION

app = FastAPI(title=PROJECT_NAME, description=DESCRIPTION, version=VERSION)


@app.exception_handler(InvalidTokenException)
async def invalid_token_handler(request: Request, exc: InvalidTokenException):
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(InactiveUserException)
async def inactive_user_handler(request: Request, exc: InactiveUserException):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(InsufficientFundsException)
async def insufficient_funds_handler(request: Request, exc: InsufficientFundsException):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(SameWalletTransferException)
async def same_wallet_handler(request: Request, exc: SameWalletTransferException):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(InactiveWalletException)
async def inactive_wallet_handler(request: Request, exc: InactiveWalletException):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(DatabaseException)
async def database_exception_handler(request: Request, exc: DatabaseException):
    return JSONResponse(
        status_code=500, content={"detail": "Error interno de base de datos"}
    )


app.include_router(health_router)
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(wallets_router, prefix=API_PREFIX)


@app.get("/")
async def read_root():
    return {"message": f"{PROJECT_NAME} — API funcionando"}
