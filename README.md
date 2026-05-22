# Prueba tecnica de Yummy Backend

FastAPI backend para prueba tecnica de yummy.

## Por qué uv en vez de pip

- **Velocidad**: resolución e instalación ~3x más rápida (Rust, descargas paralelas, caché agresiva)
- **Lockfile**: `uv.lock` garantiza builds 100% reproducibles (pip con `requirements.txt` solo fija versiones explícitas, no las transitivas)
- **Un solo binario**: reemplaza `pip` + `venv` + `virtualenv` + (opcionalmente) `pyenv`
- **Docker**: imágenes más ligeras y builds más rápidos

## Comandos reemplazados

| Acción                  | pip                                    | uv                                    |
| ----------------------- | -------------------------------------- | ------------------------------------- |
| Crear entorno virtual   | `python -m venv .venv`                 | `uv sync` (lo crea automáticamente)   |
| Instalar dependencias   | `pip install -r requirements.txt`      | `uv sync`                             |
| Agregar dependencia     | `pip install paquete` + editar req.txt | `uv add paquete`                      |
| Remover dependencia     | `pip uninstall paquete` + editar req.txt | `uv remove paquete`                 |
| Ejecutar comando        | `python -m uvicorn ...`                | `uv run uvicorn ...`                  |
| Lock de dependencias    | _(no existe)_                          | `uv lock`                             |
| Exportar requirements   | _(ya es el formato)_                   | `uv export -o requirements.txt`       |

## Desarrollo local

```bash
uv sync                        # crear .venv + instalar dependencias
uv run uvicorn app.main:app --reload --port 8020
```

## Docker

```bash
docker compose -f docker-compose-test.yml up --build
```

## Dependencias

Las dependencias están declaradas en `pyproject.toml` y fijadas en `uv.lock`.
