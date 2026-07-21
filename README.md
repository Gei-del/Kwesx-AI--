# 🌎 Kwesx AI — Inteligencia Territorial para Colombia

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=nextdotjs)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+PostGIS-336791?logo=postgresql)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Concurso](https://img.shields.io/badge/Datos%20al%20Ecosistema-2026%20Nivel%20Intermedio-orange)](https://datos.gov.co)

**Plataforma de inteligencia territorial impulsada por IA y datos abiertos de Colombia.**
Diseñada para ser usada por cualquier persona — desde campesinos hasta investigadores.

[⚡ Instalación](#instalación-rápida) · [🏗 Arquitectura](#arquitectura) · [📖 Docs](docs/) · [🤝 Contribuir](CONTRIBUTING.md)

</div>

---

## ¿Qué es Kwesx AI?

Kwesx AI convierte datos abiertos del gobierno colombiano en **inteligencia territorial comprensible** para ciudadanos, campesinos, funcionarios e investigadores.

El usuario **nunca consulta una base de datos**. Conversa con un experto que conoce su territorio.

### Fuentes de datos integradas

| Fuente | Dataset ID | Descripción | Cobertura |
|--------|-----------|-------------|-----------|
| **ANI** | `8yi9-t44c` | Tráfico vehicular en peajes nacionales | ~151,000 registros |
| **UPRA** | `gwbi-fnzs` | Índice mensual de precios de insumos agrícolas | 89 meses (2018-2026) |
| **IDEAM Precipitación** | `s54a-sgyg` | Lluvia diaria por estación hidrometeorológica | Nacional |
| **IDEAM Temperatura** | `sbwg-7ju4` | Temperatura diaria por estación | Nacional |

### Capacidades de IA

- 🧠 **Modelo IVT**  — Índice de Vulnerabilidad Territorial (Random Forest, 3 clases: BAJA/MEDIA/ALTA)
- 💬 **Asistente Conversacional** — NLP en español colombiano con intención + entidades
- 📊 **Feature Engineering Auditado** — Cruza UPRA + IDEAM con patrones estacionales reales
- 🗺️ **Mapa Territorial Interactivo** — Leaflet con estaciones climáticas georreferenciadas
- 🔮 **Simulador de Escenarios** — Qué pasa con el IVT si la lluvia cae 50% y los precios suben 10%
- ♿ **Accesibilidad Universal** — WCAG 2.2 AA, Modo Fácil, voz, alto contraste, fuentes grandes

---

## Instalación rápida

### Docker (recomendado — 1 comando)

```bash
git clone https://github.com/Gei-del/kwesx-ai--.git
cd kwesx-ai
cp .env.example .env
make up
```

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| API REST | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5433 (usuario `kwesx`) |

### Desarrollo local

**Requisitos:** Python 3.11+, Node.js 18+, PostgreSQL 15 + PostGIS

```bash
# 1. Instalar dependencias Python
pip install -r requirements.txt

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Inicializar base de datos
# Con Docker: init.sql se ejecuta solo al primer arranque del contenedor (no hace falta este paso).
# Manual (DB en puerto 5433):
psql -h localhost -p 5433 -U kwesx -d kwesx_db -f db/init.sql

# 4. Ejecutar ETL (cargar datos reales)
python -m etl.pipeline --fuente all

# 5. Entrenar modelo IA
python -m ml.train

# 6. Iniciar backend
uvicorn backend.app.main:app --reload

# 7. Iniciar frontend (nueva terminal)
cd frontend && npm install && npm run dev
```

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         KWESX AI v1.0                               │
├─────────────────┬───────────────────────┬───────────────────────────┤
│   FRONTEND      │       BACKEND         │       IA / ML             │
│  Next.js 14     │     FastAPI 0.111     │  Random Forest (IVT)      │
│  TypeScript 5   │     PostgreSQL 15     │  Feature Engineering      │
│  TailwindCSS 3  │     PostGIS 3.4       │  NLP Keyword-Based (MVP)  │
│  React 18       │     SQLAlchemy 2      │  Synthetic IDEAM Fallback │
│  React-Leaflet  │     Alembic           │  Joblib Model Persistence │
├─────────────────┴───────────────────────┴───────────────────────────┤
│                      PIPELINE ETL                                    │
│  SocrataExtractor → Normalizer → PostgresLoader → MTU Tables         │
│  (ANI + UPRA + IDEAM) · Retry + Exponential Backoff · Dry-run mode  │
├──────────────────────────────────────────────────────────────────────┤
│                  DATOS ABIERTOS — datos.gov.co                       │
│   ANI 8yi9-t44c · UPRA gwbi-fnzs · IDEAM s54a-sgyg + sbwg-7ju4     │
└──────────────────────────────────────────────────────────────────────┘
```

Arquitectura detallada → [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md)

---

## Comandos Makefile

```bash
make up          # Levantar todo (Docker Compose)
make down        # Apagar servicios
make restart     # Reiniciar backend
make logs        # Ver logs en vivo
make etl         # Pipeline ETL completo (ANI + UPRA + IDEAM)
make train       # Entrenar modelo IVT
make test        # Correr suite de pruebas
make lint        # Verificar calidad del código (flake8 + mypy)
make format      # Formatear código (black + isort)
make clean       # Limpiar cachés y archivos temporales
make shell       # Shell dentro del contenedor API
```

---

## Estructura del proyecto

```
kwesx-ai/
├── .github/              # CI/CD — GitHub Actions
│   └── workflows/
│       ├── ci.yml        # Tests + Lint en cada PR
│       └── deploy.yml    # Deploy automático a producción
├── backend/              # API FastAPI (Clean Architecture)
│   └── app/
│       ├── main.py       # Entrypoint + CORS + Routers
│       ├── config.py     # Settings (Pydantic)
│       ├── database.py   # SQLAlchemy async session
│       ├── models/       # ORM — Tablas del MTU
│       └── routers/      # Controladores HTTP
│           ├── datos.py      # /datos — ANI, UPRA, IDEAM
│           ├── asistente.py  # /asistente — Chat NLP
│           ├── prediccion.py # /prediccion — Modelo IVT
│           └── salud.py      # /salud — Health checks
├── etl/                  # Pipeline de ingesta de datos
│   ├── config.py         # Dataset IDs + API settings
│   ├── pipeline.py       # Orquestador CLI
│   ├── extractors/       # Clientes Socrata API
│   ├── transformers/     # Normalización + limpieza
│   └── loaders/          # Inserción en PostgreSQL
├── ml/                   # Machine Learning
│   ├── features.py       # Feature engineering (UPRA + IDEAM)
│   ├── modelo_territorial.py  # Random Forest IVT
│   ├── train.py          # Script de entrenamiento
│   ├── predict.py        # Servicio de inferencia
│   └── models/           # Modelos entrenados (.pkl)
├── frontend/             # Next.js 14 App Router
│   └── src/
│       ├── app/          # Páginas (Dashboard, Asistente, Datos, IVT)
│       ├── components/   # UI Components (Layout, Cards, Charts, Map)
│       ├── contexts/     # AppContext (accesibilidad, Modo Fácil)
│       └── lib/          # API client tipado
├── data/                  # Datos organizados por etapa del pipeline
│   ├── 01_raw/           # Datos crudos de la API
│   ├── 02_external/      # Datos de referencia (DANE, etc.)
│   ├── 03_processed/     # Datos limpios y normalizados
│   ├── 04_feature_store/ # Features para el modelo
│   ├── 05_training/      # Datasets de entrenamiento
│   ├── 06_validation/    # Datasets de validación
│   └── 07_predictions/   # Predicciones históricas
├── docs/                 # Documentación técnica completa
├── tests/                # Suite de pruebas (unit + integration)
│   ├── backend/
│   ├── ml/
│   └── etl/
├── deploy/               # Configuraciones de despliegue
│   ├── docker/
│   ├── vercel/
│   └── render/
├── db/                   # Esquema de base de datos
│   └── init.sql
├── .env.example          # Variables de entorno de ejemplo
├── docker-compose.yml    # Orquestación Docker
├── Makefile              # Comandos de desarrollo
├── pyproject.toml        # Configuración Python (black, mypy, pytest)
└── requirements.txt      # Dependencias Python
```

---

## Concurso: Datos al Ecosistema 2026

**Convocatoria:** Ministerio de TIC de Colombia + datos.gov.co  
**Nivel:** Intermedio  
**Entregas:** Entrega 1 (1 julio 2026) · Entrega 2 (13-17 julio 2026)

**Propuesta de valor:** Democratizar el acceso a datos territoriales complejos mediante IA conversacional, visualizaciones intuitivas y accesibilidad universal — para que un campesino, una comunidad indígena o un investigador puedan comprender el estado de su territorio en menos de 2 minutos.

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | Diseño técnico completo |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Plan de desarrollo y sprints |
| [docs/BITACORA.md](docs/BITACORA.md) | Registro de decisiones técnicas |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guía de contribución |
| [SECURITY.md](SECURITY.md) | Política de seguridad |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios |

---

## Contribuir

¿Quieres mejorar Kwesx AI? Lee [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Licencia

MIT © 2026 — Kwesx AI Team. Ver [LICENSE](LICENSE).

---

<div align="center">
Hecho con ❤️ para Colombia · Datos oficiales de <a href="https://datos.gov.co">datos.gov.co</a>
</div>

> Documento base del proyecto: `Kwesx_AI_Documentacion_Profesional.docx` (visión completa, sin recorte de alcance).
> Los documentos en `docs/` son la versión de trabajo, ajustada a un sprint de **menos de 1 mes**.

## Cómo navegar este repo

| Carpeta / Archivo | Qué contiene |
|---|---|
| `docs/ROADMAP.md` | Plan semana a semana. **Empieza aquí** para saber en qué fase estamos. |
| `docs/ARQUITECTURA.md` | Stack técnico, capas del sistema, modelo de datos (Modelo Territorial Unificado). |
| `docs/BITACORA.md` | Diario cronológico: qué se decidió, qué se construyó y por qué, sesión por sesión. |
| `docs/EQUIPO.md` | Quién es quién y qué rol cumple cada persona del equipo. |
| `backend/` | API en Python (FastAPI). Lógica de negocio, ETL, modelos de IA. |
| `frontend/` | Aplicación web en Next.js/React (dashboard, asistente, mapas). |
| `etl/` | Scripts de extracción, limpieza e integración de datasets. |
| `data/` | Datos crudos (`raw/`) y procesados (`processed/`). **No se sube a git** (ver `.gitignore`). |

## Estado actual

✅ **Versión 1.0.0 — MVP completo y funcional** (Entrega 2 del concurso, julio 2026): ETL con 5 fuentes de datos, 5 modelos de ML, asistente conversacional, dashboard, mapa interactivo y accesibilidad WCAG 2.2 AA.

Ver `docs/BITACORA.md` para el historial completo de desarrollo y `CHANGELOG.md` para el detalle de la versión.
