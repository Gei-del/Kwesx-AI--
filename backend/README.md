# Kwesx AI — Backend

**Stack:** Python 3.11 · FastAPI 0.111 · SQLAlchemy 2.0 async · PostgreSQL 15 + PostGIS

API REST que sirve datos del Modelo Territorial Unificado (MTU), el Asistente IA y los modelos ML.

---

## Configuracion rapida

```bash
# Desde la raiz del proyecto
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Variables de entorno (ya existe .env.example)
cp .env.example .env

# Correr en desarrollo
make backend
# o
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

API: http://localhost:8000  
Swagger UI: http://localhost:8000/docs  
ReDoc: http://localhost:8000/redoc

---

## Endpoints principales

| Metodo | Ruta | Descripcion |
|---|---|---|
| GET | `/` | Estado general de la API |
| GET | `/salud` | Health check |
| GET | `/salud/etl` | Estado de todas las tablas MTU |
| GET | `/datos/upra` | Serie de precios agricolas UPRA |
| GET | `/datos/ani` | Trafico vehicular peajes ANI |
| GET | `/datos/ideam` | Variables climaticas IDEAM |
| GET | `/datos/conectividad` | Brecha digital por municipio |
| GET | `/datos/educacion` | Cobertura educativa MEN |
| POST | `/asistente/chat` | Consulta en lenguaje natural |
| GET | `/prediccion/actual` | IVT con datos recientes |
| POST | `/prediccion/simular` | IVT con parametros personalizados |
| GET | `/ml/insights` | Todos los insights ML |
| GET | `/ml/forecast/{serie}` | Pronostico de serie temporal |
| GET | `/ml/anomalias` | Anomalias detectadas |
| GET | `/ml/clustering` | Segmentacion territorial |
| GET | `/ml/explicacion` | Explicacion SHAP |
| GET | `/recomendaciones` | Recomendaciones IA priorizadas |

Ver documentacion completa: [docs/API.md](../docs/API.md)

---

## Estructura

```
backend/
├── app/
│   ├── main.py           # FastAPI app + lifespan (tablas se crean automaticamente)
│   ├── config.py         # Settings con Pydantic (carga .env)
│   ├── database.py       # Engine async + SessionLocal
│   ├── models/mtu.py     # SQLAlchemy models (5 tablas MTU)
│   ├── ml/
│   │   ├── nlp_intent.py     # NLP: TF-IDF + coseno, 8 intenciones
│   │   └── recommender.py    # Sistema de recomendaciones territoriales
│   └── routers/
│       ├── salud.py          # /salud
│       ├── datos.py          # /datos/*
│       ├── asistente.py      # /asistente/*
│       ├── prediccion.py     # /prediccion/*
│       ├── ml_avanzado.py    # /ml/*
│       └── recomendaciones.py # /recomendaciones
└── etl/
    └── extractors/           # Conectores DANE/MinTIC y MEN-SIMAT
```

---

## Base de datos

Las tablas se crean automaticamente al arrancar el backend. Para cargar datos:

```bash
make etl        # Todos los datasets
make etl-upra   # Solo UPRA
```

Ver esquema completo: [docs/DATABASE.md](../docs/DATABASE.md)

---

## Seguridad

- CORS solo acepta origenes en `ALLOWED_ORIGINS`
- Rate limiting por endpoint
- Sin credenciales hardcodeadas
- Validacion Pydantic en todos los endpoints

---

## Tests

```bash
pytest tests/ -v
```

---

## Produccion (Render)

Variables requeridas:
```
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=<openssl rand -hex 32>
DEBUG=false
ALLOWED_ORIGINS=https://kwesx.vercel.app
SOCRATA_APP_TOKEN=<token>
```
