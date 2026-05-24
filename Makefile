.PHONY: help build up down restart logs migrate test

help:
	@echo "Comandos disponibles:"
	@echo "  make build     — construir las imágenes de Docker"
	@echo "  make up        — levantar el servidor y la base de datos"
	@echo "  make down      — bajar los contenedores"
	@echo "  make restart   — bajar y volver a levantar"
	@echo "  make migrate   — correr las migraciones dentro del contenedor"
	@echo "  make test      — correr los tests dentro del contenedor"
	@echo "  make logs      — ver los logs del servidor en tiempo real"
	@echo "  make setup     — primera vez: copiar .env + levantar + migrar"

build:
	docker compose -f docker-compose.local.yml build

up:
	docker compose -f docker-compose.local.yml up

down:
	docker compose -f docker-compose.local.yml down

restart: down up

logs:
	docker compose -f docker-compose.local.yml logs -f server

migrate:
	docker compose -f docker-compose.local.yml exec server alembic upgrade head

test:
	docker compose -f docker-compose.local.yml exec server pytest tests/ -v

setup:
	@test -f .env || cp .env.example .env
	docker compose -f docker-compose.local.yml up --build -d
	@echo "Esperando que el servidor esté listo..."
	@sleep 5
	docker compose -f docker-compose.local.yml exec server alembic upgrade head
	@echo "Listo. API disponible en http://localhost:8020"
	@echo "Swagger en http://localhost:8020/docs"
