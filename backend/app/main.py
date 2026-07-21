"""
backend/app/main.py
====================
Punto de entrada de la API FastAPI de Kwesx AI.

Para correr en desarrollo:
  uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

Con Docker Compose:
  docker compose up -d

Documentacion automatica (Swagger UI): http://localhost:8000/docs
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import text

from backend.app.config import settings
from backend.app.database import engine
from backend.app.models.mtu import Base
from backend.app.routers import asistente, datos, salud
from backend.app.routers import ml_avanzado, prediccion, recomendaciones


# -- Startup / Shutdown --------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea las tablas del MTU al arrancar si no existen."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.success("Tablas MTU verificadas/creadas.")
    except Exception as e:
        logger.warning(f"No se pudo verificar tablas al inicio: {e}")
    yield
    # Shutdown: liberar pool de conexiones
    await engine.dispose()

# -- Rate Limiter (slowapi -- opcional, no rompe si no esta instalado) ---------
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
    limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
    RATE_LIMITING = True
except ImportError:
    limiter = None
    RATE_LIMITING = False
    logger.warning("slowapi no instalado - rate limiting desactivado")

# -- Aplicacion ----------------------------------------------------------------
app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.PROJECT_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Datos MTU",          "description": "Datos abiertos: ANI, UPRA, IDEAM, DANE, MinTIC"},
        {"name": "Asistente IA",       "description": "Asistente conversacional con NLP territorial"},
        {"name": "IA Avanzada",        "description": "Ensemble, clustering, forecasting, anomalias, XAI"},
        {"name": "Prediccion",         "description": "Indice de Vulnerabilidad Territorial (IVT)"},
        {"name": "Salud",              "description": "Estado del sistema y ETL"},
        {"name": "Recomendaciones IA", "description": "Recomendaciones territoriales priorizadas"},
    ],
    contact={"name": "Kwesx AI", "email": "gpontonca@gmail.com"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

# -- Rate Limiting -------------------------------------------------------------
if RATE_LIMITING and limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# -- CORS ----------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://kwesx-ai.vercel.app",
]
if settings.debug:
    ALLOWED_ORIGINS.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    # Permite previews de Vercel (https://<algo>.vercel.app)
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)


# -- Security Headers ----------------------------------------------------------
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(self)"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# -- Request logging -----------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0 = datetime.now()
    response = await call_next(request)
    ms = (datetime.now() - t0).total_seconds() * 1000
    if request.url.path not in ("/salud", "/salud/etl"):  # skip health checks
        logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({ms:.0f}ms)")
    return response


# -- Global error handler ------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error en {request.method} {request.url.path}: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno",
            "mensaje": "No pudimos procesar tu solicitud en este momento. Intenta de nuevo en unos segundos.",
        },
    )


# -- Routers -------------------------------------------------------------------
app.include_router(datos.router)
app.include_router(asistente.router)
app.include_router(salud.router)
app.include_router(prediccion.router)
app.include_router(ml_avanzado.router)
app.include_router(recomendaciones.router)


# -- Root ----------------------------------------------------------------------
@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz: estado de la API."""
    return {
        "proyecto": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "descripcion": (
            "Sistema Operativo Territorial Inteligente para Colombia. "
            "Datos abiertos + IA = conocimiento ciudadano."
        ),
        "docs": "/docs",
        "estado": "activo",
        "ambiente": settings.ENVIRONMENT,
        "endpoints": {
            "datos":           "/datos",
            "asistente":       "/asistente",
            "prediccion":      "/prediccion",
            "ml":              "/ml",
            "recomendaciones": "/recomendaciones",
            "salud":           "/salud",
        },
        "nlp": "TF-IDF + cosine similarity (scikit-learn)",
        "datasets": ["ANI", "UPRA", "IDEAM", "DANE", "MinTIC", "MEN"],
        "modelos_ia": [
            "Random Forest", "XGBoost", "KMeans", "DBSCAN",
            "Holt-Winters", "SARIMA", "Isolation Forest", "LOF", "SHAP",
        ],
    }
