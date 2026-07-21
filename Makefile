# ============================================================
# Kwesx AI — Makefile
# Comandos de desarrollo, testing y despliegue.
# Uso: make <target>
# ============================================================

.PHONY: help up down restart logs shell etl train validate test lint format clean build

# ── Ayuda ────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  🌎 Kwesx AI — Comandos disponibles"
	@echo "  ─────────────────────────────────────────────────"
	@echo "  make up         Levantar todos los servicios (Docker)"
	@echo "  make down       Apagar todos los servicios"
	@echo "  make restart    Reiniciar el backend"
	@echo "  make logs       Ver logs en vivo"
	@echo "  make shell      Abrir shell en el contenedor API"
	@echo ""
	@echo "  make etl              Ejecutar pipeline ETL completo"
	@echo "  make etl-ani          ETL solo ANI (peajes)"
	@echo "  make etl-upra         ETL solo UPRA (precios)"
	@echo "  make etl-ideam        ETL solo IDEAM (clima)"
	@echo "  make etl-conectividad ETL solo Conectividad (DANE+MinTIC)"
	@echo "  make etl-educacion    ETL solo Educación (MEN-SIMAT)"
	@echo "  make train            Entrenar modelo IVT"
	@echo "  make validate         Calcular métricas ML y guardar en JSON"
	@echo ""
	@echo "  make test       Correr suite de pruebas"
	@echo "  make test-fast  Pruebas rápidas (sin integración)"
	@echo "  make lint       Verificar calidad del código"
	@echo "  make format     Formatear código automáticamente"
	@echo ""
	@echo "  make build      Construir imagen Docker"
	@echo "  make clean      Limpiar archivos temporales"
	@echo "  make setup      Configuración inicial del proyecto"
	@echo ""

# ── Docker ───────────────────────────────────────────────────
up:
	@echo "🚀 Levantando Kwesx AI..."
	docker compose up -d
	@echo "✅ Servicios activos:"
	@echo "   Frontend: http://localhost:3000"
	@echo "   API:      http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"

down:
	@echo "🛑 Apagando servicios..."
	docker compose down

restart:
	@echo "🔄 Reiniciando backend..."
	docker compose restart api

logs:
	docker compose logs -f api

logs-db:
	docker compose logs -f db

shell:
	docker compose exec api bash

build:
	docker compose build --no-cache

# ── ETL ─────────────────────────────────────────────────────
etl:
	@echo "📦 Ejecutando pipeline ETL completo..."
	python -m etl.pipeline --fuente all

etl-ani:
	python -m etl.pipeline --fuente ani

etl-upra:
	python -m etl.pipeline --fuente upra

etl-ideam:
	python -m etl.pipeline --fuente ideam

etl-conectividad:
	python -m etl.pipeline --fuente conectividad

etl-educacion:
	python -m etl.pipeline --fuente educacion

etl-dry:
	python -m etl.pipeline --fuente all --dry-run

# ── Machine Learning ─────────────────────────────────────────
train:
	@echo "🧠 Entrenando modelo IVT (Random Forest)..."
	python -m ml.train

train-force:
	python -m ml.train --force

train-advanced:
	@echo "🚀 Entrenando todos los modelos ML avanzados..."
	python -m ml.train_advanced

train-advanced-force:
	python -m ml.train_advanced --force

train-ensemble:
	python -m ml.train_advanced --modelo ensemble

train-clustering:
	python -m ml.train_advanced --modelo clustering

train-forecasting:
	python -m ml.train_advanced --modelo forecasting

train-anomaly:
	python -m ml.train_advanced --modelo anomaly

train-xai:
	python -m ml.train_advanced --modelo xai

validate:
	@echo "📊 Calculando métricas de validación del modelo..."
	python -m ml.validation_report

# ── Testing ──────────────────────────────────────────────────
test:
	@echo "🧪 Ejecutando suite de pruebas..."
	python -m pytest tests/ -v --tb=short

test-fast:
	python -m pytest tests/ -v -m "not integration" --tb=short

test-backend:
	python -m pytest tests/backend/ -v --tb=short

test-ml:
	python -m pytest tests/ml/ -v --tb=short

test-etl:
	python -m pytest tests/etl/ -v --tb=short

test-coverage:
	python -m pytest tests/ --cov=backend --cov=ml --cov=etl \
		--cov-report=html:reports/coverage \
		--cov-report=term-missing

# ── Calidad de código ────────────────────────────────────────
lint:
	@echo "🔍 Verificando calidad del código..."
	flake8 backend/ etl/ ml/ --max-line-length=100 --exclude=__pycache__
	mypy backend/ ml/ --ignore-missing-imports --no-strict-optional

format:
	@echo "✨ Formateando código..."
	black backend/ etl/ ml/ --line-length=100
	isort backend/ etl/ ml/ --profile=black

format-check:
	black backend/ etl/ ml/ --check --line-length=100

# ── Setup inicial ────────────────────────────────────────────
setup:
	@echo "⚙️  Configurando proyecto Kwesx AI..."
	@test -f .env || cp .env.example .env
	pip install -r requirements.txt
	cd frontend && npm install
	mkdir -p data/01_raw data/02_external data/03_processed \
	         data/04_feature_store data/05_training data/06_validation \
	         data/07_predictions data/08_exports data/09_backups \
	         ml/models reports logs
	@echo "✅ Setup completado. Próximos pasos:"
	@echo "   1. Editar .env con tus credenciales"
	@echo "   2. make up (levantar Docker)"
	@echo "   3. make etl (cargar datos)"
	@echo "   4. make train (entrenar modelo)"

setup-dev: setup
	pip install pytest pytest-asyncio pytest-cov httpx
	pip install black isort flake8 mypy

# ── Limpieza ─────────────────────────────────────────────────
clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf reports/coverage 2>/dev/null || true
	@echo "✅ Limpieza completada"

clean-frontend:
	cd frontend && rm -rf .next node_modules

clean-all: clean clean-frontend

# ── Producción ───────────────────────────────────────────────
deploy-check:
	@echo "🚀 Verificando preparación para producción..."
	@test -f .env || (echo "❌ .env no existe. Copia .env.example" && exit 1)
	@test -f ml/models/ivt_model.pkl || (echo "⚠️  Modelo no entrenado. Ejecuta: make train")
	@echo "✅ Verificación completada"

# ── Frontend ─────────────────────────────────────────────────
frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-lint:
	cd frontend && npm run lint
