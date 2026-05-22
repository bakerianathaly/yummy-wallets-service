import os

from starlette.config import Config

config = Config(".env")

PROJECT_NAME = "Yummy Wallet"
DESCRIPTION = "Servicio de wallets para el producto fintech de Yummy"
DEBUG: bool = False
TIMEZONE: str = "America/Caracas"

VERSION = "1.0.0"
API_PREFIX = "/api/v1"

DATABASE_URL = config("DATABASE_URL", cast=str, default="sqlite+aiosqlite:///./dev.db")

SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
