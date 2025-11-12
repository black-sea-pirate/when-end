# Makefile for Countdowns Development

.PHONY: help up down restart logs build clean test migrate shell

help:
	@echo "Countdowns - Development Commands"
	@echo ""
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - Show logs (use CTRL+C to exit)"
	@echo "  make build       - Rebuild all containers"
	@echo "  make clean       - Stop and remove all containers and volumes"
	@echo "  make test        - Run backend tests"
	@echo "  make migrate     - Run database migrations"
	@echo "  make shell       - Open backend shell"
	@echo "  make db-shell    - Open PostgreSQL shell"
	@echo "  make install     - Install frontend dependencies"
	@echo ""

up:
	docker compose up -d
	@echo "Services started! Access at http://localhost:3000"

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

build:
	docker compose build --no-cache

clean:
	docker compose down -v
	@echo "All containers and volumes removed"

test:
	docker compose exec backend pytest tests/ -v

migrate:
	docker compose exec backend alembic upgrade head

shell:
	docker compose exec backend sh

db-shell:
	docker compose exec db psql -U countdowns countdowns_db

install:
	cd frontend && npm install
	cd backend && pip install -r requirements.txt

# Development shortcuts
dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev
