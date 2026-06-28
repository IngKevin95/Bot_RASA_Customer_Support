.DEFAULT_GOAL := help
RASA_MODEL_NAME ?= latest

.PHONY: help train test test-cov test-nlu actions run shell docker-up docker-down lint backend backend-install frontend-serve all-up all-down

help: ## Muestra esta ayuda
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# --- Entrenamiento ---

train: ## Entrena el modelo NLU
	rasa train --fixed-model-name $(RASA_MODEL_NAME)

# --- Testing ---

test: ## Corre los tests unitarios
	pytest tests/test_actions.py

test-cov: ## Tests con reporte de cobertura
	pytest tests/ --cov=actions --cov-report=term-missing --cov-fail-under=80

test-nlu: ## Evalua el modelo NLU (requiere modelo entrenado)
	rasa test nlu --nlu data/nlu.yml

# --- Servidor local ---

actions: ## Inicia el action server en puerto 5055
	rasa run actions --port 5055

run: ## Inicia RASA con API REST en puerto 5005
	rasa run --enable-api --cors "*" --port 5005 --endpoints endpoints.yml

shell: ## Inicia el shell interactivo de RASA
	rasa shell

# --- Docker ---

docker-up: ## Levanta el entorno completo con docker-compose
	docker compose up --build

docker-down: ## Detiene docker-compose
	docker compose down

# --- Validacion ---

lint: ## Valida estructura y consistencia de los datos de entrenamiento
	rasa data validate --data data/ --domain domain.yml

# --- Backend ---

backend: ## Inicia el backend FastAPI en modo desarrollo (:8000)
	cd backend && uvicorn app.main:app --reload --port 8000

backend-install: ## Instala dependencias del backend
	pip install -r backend/requirements.txt

# --- Frontend ---

frontend-serve: ## Sirve el frontend localmente en :8080 (sin Docker)
	python -m http.server 8080 -d frontend

# --- Stack completo ---

all-up: ## Levanta toda la arquitectura con Docker Compose
	docker compose up --build

all-down: ## Detiene y elimina volumenes del stack completo
	docker compose down -v
