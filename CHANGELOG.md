# Changelog — Kwesx AI

Todos los cambios notables de este proyecto se documentan en este archivo.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).
Versionado siguiendo [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Pendiente
- Integración con API del DANE (códigos municipales)
- Tests de integración end-to-end (Playwright)
- Soporte para idiomas indígenas (Wayuunaiki, Nasa Yuwe)
- Dashboard de administración para monitoreo del ETL

---

## [1.0.0] — 2026-07-02

### Concurso: Datos al Ecosistema 2026 — Nivel Intermedio

Primera versión funcional del sistema, presentada para la Entrega 1 del concurso.

### Agregado
- **Frontend (Next.js 14)**
  - Dashboard "Hoy en tu territorio" con InsightCards y chips de preguntas frecuentes
  - Asistente conversacional con reconocimiento de voz (`lang="es-CO"`)
  - Páginas de datos: `/datos/upra`, `/datos/ani`, `/datos/ideam`
  - Modo Fácil (lenguaje humano, emojis, fuentes grandes)
  - Modo Alto Contraste (WCAG 2.2 AA)
  - Selector de tamaño de fuente (normal / grande / muy grande)
  - Botón flotante de alertas territoriales (FAB)
  - Mapa interactivo con React-Leaflet
  - `AppContext` con persistencia en `localStorage`

- **Backend (FastAPI 0.111)**
  - Router `/datos` — endpoints para ANI, UPRA, IDEAM con filtros y paginación
  - Router `/asistente` — NLP keyword-based en español colombiano
  - Router `/prediccion` — modelo IVT con score y clasificación
  - Router `/salud` — health check para Docker

- **ML — Modelo IVT**
  - Random Forest Classifier con 3 clases (BAJA / MEDIA / ALTA)
  - Feature engineering: UPRA 40% + IDEAM clima 35% + temporal 25%
  - Thresholds calibrados: `MEDIA=25.0`, `ALTA=42.0`
  - Fallback sintético IDEAM basado en normales 1961-2020
  - Serialización con joblib (`ml/models/ivt_model.pkl`)

- **ETL Pipeline**
  - Extractor Socrata genérico con paginación y retry exponencial
  - 3 extractores: ANI (`8yi9-t44c`), UPRA (`gwbi-fnzs`), IDEAM (`s54a-sgyg`, `sbwg-7ju4`)
  - Normalización, limpieza y carga en PostgreSQL + PostGIS
  - Modo dry-run para validación sin escritura

- **Infraestructura**
  - Docker Compose con servicios: API + PostgreSQL 15 + PostGIS 3.4
  - Makefile con 30+ targets (etl, train, test, lint, format, clean, deploy-check)
  - `pyproject.toml` con black, isort, mypy, pytest, coverage
  - CI/CD con GitHub Actions (ci.yml — lint + test; deploy.yml — producción)
  - Estructura de carpetas `data/01_raw` → `data/09_backups`
  - Estructura de tests `tests/backend/`, `tests/ml/`, `tests/etl/`

- **Documentación**
  - README.md profesional con badges, arquitectura, comandos
  - CONTRIBUTING.md con convención de commits y estándares
  - SECURITY.md con política de vulnerabilidades
  - CODE_OF_CONDUCT.md basado en Contributor Covenant
  - LICENSE MIT

### Corregido
- `pd.to_period()` removido en pandas 2.x → migrado a `series.dt.to_period("M")`
- `classification_report` crash cuando clase ALTA no aparecía en datos sintéticos
  - Fix: `labels=clases_test, target_names=nombres_test, zero_division=0` (dinámico)
- `stratify` crash con clases de 1 solo sample → condicional `min_samples_por_clase >= 2`
- Null bytes en `backend/app/main.py` de sesiones anteriores
- `ChunkLoadError` de Next.js por caché `.next` desactualizado tras refactor mayor

### Diseño
- Nueva paleta: verde esmeralda colombiano (`#1A6B42`) + ámbar (`#F59E0B`)
- CSS variables para diseño adaptativo: `--color-terra`, `--font-size-base`, etc.
- Atributos `data-mode`, `data-font`, `data-contrast` en `<html>` para estilos globales
- Componentes CSS: `.card`, `.btn-primary`, `.sidebar-item`, `.question-chip`, `.insight-card`, `.fab`, `.skeleton`
- Animaciones: `fadeIn`, `slideUp`, `slideInRight`, `pop`, `pulseSoft`, `shimmer`

---

## [0.1.0] — 2026-06-01

### Prototipo inicial

- Exploración de datasets disponibles en datos.gov.co
- Prototipo de modelo IVT básico (thresholds sin calibrar)
- Estructura inicial del proyecto (sin Docker, sin tests)

---

[Unreleased]: https://github.com/tu-usuario/kwesx-ai/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/tu-usuario/kwesx-ai/releases/tag/v1.0.0
[0.1.0]: https://github.com/tu-usuario/kwesx-ai/releases/tag/v0.1.0
