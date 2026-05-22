from starlette.config import Config

config = Config(".env")

PROJECT_NAME = "Cronicos"
DESCRIPTION = "Sistema de Pacientes Cronicos de Venemergencia"
DEBUG: bool = False
TIMEZONE: str = "America/Caracas"

VERSION = "1.0.0"
API_PREFIX = "/api/v1"

DATABASE_URL = config("DATABASE_URL", cast=str)
