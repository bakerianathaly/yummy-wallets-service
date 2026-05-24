# Yummy Wallet — Prueba Técnica Backend

Backend de billetera digital construido con FastAPI + PostgreSQL. 

Permite a los usuarios registrarse, crear su wallet y operar con ella: depositar, retirar, transferir y consultar
su historial. El foco principal del proyecto estuvo en garantizar que las operaciones concurrentes (dos retiros al mismo tiempo, transferencias cruzadas) no corrompan los saldos.

Para entender las decisiones de diseño y por qué el sistema funciona como funciona, leer `DESIGN.md`.

---

## Requisitos

- [Docker](https://www.docker.com/) y Docker Compose — para levantar con un solo comando
- [uv](https://docs.astral.sh/uv/) — si querés correr en local sin Docker

---

## Levantar con Docker (recomendado)

```bash
# 1. Copiar las variables de entorno
cp .env.example .env

# 2. Levantar todo (API + PostgreSQL)
docker compose -f docker-compose.local.yml up --build

# 3. Correr las migraciones, dentro dle contenedor
# Hay que ejecutarlas las migraciones, en otra terminal, con los contenedores ya corriendo
# Eso aplica todas las migraciones pendientes contra el PostgreSQL del contenedor. Solo hace falta correrlo la primera vez (o cuando haya migraciones nuevas).
docker compose -f docker-compose.local.yml exec server alembic upgrade head

# Para correr los test, en otra terminal, con los contenedores ya corriendo
docker compose -f docker-compose.local.yml exec server pytest tests/ -v
```

La API queda disponible en `http://localhost:8020`.

La documentación interactiva (Swagger) está en `http://localhost:8020/docs` — desde ahí
se pueden probar todos los endpoints directamente en el navegador.

---
## Levantar con ayuda del Makefile

Para la primera vez, solo necesitas estos 3 pasos:

1. Instalar make (si no lo tenés)
  - macOS
  brew install make

2. Copiar el .env y ajustar las variables si querés cambiar algo (contraseña, secret key, etc.)
  cp .env.example .env

3. Levantar todo
  make setup

Ese único comando construye las imágenes, levanta el servidor + PostgreSQL, espera que estén listos y corre las migraciones. Al final te dice que la API está en http://localhost:8020.

Del día a día en adelante:
```bash
make up        # levantar
make down      # bajar
make logs      # ver qué está pasando
make test      # correr tests
make migrate   # si hay migraciones nuevas
```
---

## Correr en local sin Docker

Requiere tener `uv` instalado y Python 3.12.

```bash
# Instalar dependencias y crear el entorno virtual
uv sync

# Copiar variables de entorno y ajustar DATABASE_URL a tu Postgres local
cp .env.example .env

# Correr las migraciones
uv run alembic upgrade head

# Levantar el servidor
uv run uvicorn app.main:app --reload --port 8020
```

---

## Variables de entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DATABASE_URL` | URL de conexión a PostgreSQL | `postgresql+asyncpg://user:pass@localhost:5432/yummy` |
| `SECRET_KEY` | Clave para firmar los JWT — cambiar en producción | `una-cadena-larga-y-aleatoria` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Minutos de validez del token | `30` |
| `DB_USER` | Usuario de PostgreSQL (usado por Docker) | `user` |
| `DB_PASSWORD` | Contraseña de PostgreSQL (usado por Docker) | `password` |
| `DB_NAME` | Nombre de la base de datos (usado por Docker) | `yummy_wallet` |

---

## Correr los tests

Los tests corren contra SQLite en memoria — no necesitan Docker ni Postgres.

```bash
# Todos los tests
uv run pytest tests/ -v

# Solo los tests de un módulo específico
uv run pytest tests/services/test_transfer_wallet.py -v

# Con reporte de cobertura
uv run pytest tests/ --tb=short -q
```

---

## Endpoints

Todos bajo el prefijo `/api/v1` excepto `/health`.

### Autenticación

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servidor |
| `POST` | `/api/v1/auth/register` | Crear cuenta de usuario |
| `POST` | `/api/v1/auth/login` | Iniciar sesión — devuelve JWT |

### Usuarios (requieren JWT)

| Método | Ruta | Descripción |
|---|---|---|
| `PUT` | `/api/v1/users/me` | Actualizar nombre, email o contraseña |
| `DELETE` | `/api/v1/users/me` | Desactivar cuenta (soft delete) |

### Wallet (requieren JWT)

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/wallets/` | Crear wallet (una por usuario) del ususario logeado (el que viaja en el token) |
| `POST` | `/api/v1/wallets/{id}/deposit` | Depositar dinero |
| `POST` | `/api/v1/wallets/{id}/withdraw` | Retirar dinero |
| `POST` | `/api/v1/wallets/{id}/transfer` | Transferir a otra wallet |
| `GET` | `/api/v1/wallets/me` | Saldo actual + últimas 10 transacciones del ususario logeado (el que viaja en el token) |
| `GET` | `/api/v1/wallets/me/transactions` | Historial paginado (`?page=1&page_size=20`) del ususario logeado (el que viaja en el token) |

### Cómo autenticarse

```bash
# 1. Registrarse
curl -X POST http://localhost:8020/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "maria@ejemplo.com", "full_name": "María", "password": "Password123"}'

# 2. Hacer login y copiar el access_token
curl -X POST http://localhost:8020/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "maria@ejemplo.com", "password": "Password123"}'

# 3. Usar el token en los siguientes requests
curl -X POST http://localhost:8020/api/v1/wallets/ \
  -H "Authorization: Bearer <token>"
```

Los depósitos, retiros y transferencias requieren un campo `idempotency_key` — un UUID generado por el cliente que garantiza que si el request se reenvía por problemas de red, la operación no se ejecuta dos veces:

```bash
curl -X POST http://localhost:8020/api/v1/wallets/<wallet_id>/deposit \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100.00,
    "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
    "description": "Recarga de prueba"
  }'
```

---

## Stack

| Capa | Tecnología |
|---|---|
| Framework | FastAPI 0.115 + Uvicorn |
| ORM | SQLModel (SQLAlchemy + Pydantic) |
| Base de datos | PostgreSQL 16 (asyncpg) |
| Auth | JWT (python-jose) + bcrypt |
| Migraciones | Alembic |
| Package manager | uv |
| Tests | pytest + pytest-asyncio |
| Python | 3.12 |

---

## Por qué uv en vez de pip

| Acción | pip | uv |
|---|---|---|
| Instalar dependencias | `pip install -r requirements.txt` | `uv sync` |
| Agregar dependencia | `pip install paquete` + editar archivo | `uv add paquete` |
| Remover dependencia | `pip uninstall paquete` + editar archivo | `uv remove paquete` |
| Ejecutar comando | `python -m uvicorn ...` | `uv run uvicorn ...` |

`uv` crea el entorno virtual automáticamente con `uv sync`, garantiza builds reproducibles
via `uv.lock` (fija todas las dependencias transitivas, no solo las directas), y es
significativamente más rápido que pip.
