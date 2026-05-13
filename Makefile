SHELL := /bin/bash

BACKEND_DIR := backend
BACKEND_VENV := $(BACKEND_DIR)/.venv
BACKEND_UVICORN := $(BACKEND_VENV)/bin/uvicorn
BACKEND_APP := main:app
BACKEND_HOST := 127.0.0.1
BACKEND_PORT := 8001

FRONTEND_HOST := 127.0.0.1
FRONTEND_PORT := 5173

.PHONY: help check-backend check-frontend dev-backend dev-frontend dev

help:
	@printf "Targets disponibles:\n"
	@printf "  make dev           Levanta backend y frontend en modo desarrollo\n"
	@printf "  make dev-backend   Levanta FastAPI con reload\n"
	@printf "  make dev-frontend  Levanta Vite para el frontend\n"

check-backend:
	@test -x "$(BACKEND_UVICORN)" || (echo "Falta $(BACKEND_UVICORN). Crea el venv e instala dependencias en backend/." && exit 1)

check-frontend:
	@command -v npm >/dev/null 2>&1 || (echo "npm no esta disponible en PATH." && exit 1)
	@test -d node_modules || (echo "Falta node_modules. Ejecuta npm install en la raiz del proyecto." && exit 1)

dev-backend: check-backend
	cd $(BACKEND_DIR) && .venv/bin/uvicorn $(BACKEND_APP) --reload --host $(BACKEND_HOST) --port $(BACKEND_PORT)

dev-frontend: check-frontend
	npm run dev -- --host $(FRONTEND_HOST) --port $(FRONTEND_PORT)

dev: check-backend check-frontend
	@set -m; \
	trap 'kill 0' INT TERM EXIT; \
	cd $(BACKEND_DIR) && .venv/bin/uvicorn $(BACKEND_APP) --reload --host $(BACKEND_HOST) --port $(BACKEND_PORT) & \
	npm run dev -- --host $(FRONTEND_HOST) --port $(FRONTEND_PORT) & \
	wait
