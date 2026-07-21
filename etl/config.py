"""
etl/config.py
=============
Configuración central del ETL de Kwesx AI.

Carga variables de entorno desde .env (usa python-dotenv).
Todos los extractores importan sus constantes desde aquí,
así que cambiar un ID de dataset o URL solo requiere tocar este archivo.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Socrata / datos.gov.co ──────────────────────────────────────────────────
SOCRATA_BASE = "https://www.datos.gov.co/resource"
SOCRATA_TOKEN = os.getenv("SOCRATA_APP_TOKEN", "")  # opcional, sin token funciona

# Headers que se envían en cada request a la API
SOCRATA_HEADERS: dict = {
    "Accept": "application/json",
}
if SOCRATA_TOKEN:
    SOCRATA_HEADERS["X-App-Token"] = SOCRATA_TOKEN

# ── Dataset IDs (confirmados en exploración 2026-06-30) ────────────────────
ANI_DATASET_ID = os.getenv("ANI_DATASET_ID", "8yi9-t44c")
# ANI Tráfico Vehicular: 151,453 filas, por peaje/categoría/período

UPRA_DATASET_ID = os.getenv("UPRA_DATASET_ID", "gwbi-fnzs")
# UPRA Índice Precios Insumos Agrícolas: 89 filas, serie mensual nacional 2021–2026

IDEAM_PRECIPITACION_ID = os.getenv("IDEAM_PRECIPITACION_ID", "s54a-sgyg")
# IDEAM Precipitación: estaciones meteorológicas, datos cada 10 min, actualización diaria

IDEAM_TEMPERATURA_ID = os.getenv("IDEAM_TEMPERATURA_ID", "sbwg-7ju4")
# IDEAM Temperatura Ambiente del Aire: mismo schema que precipitación, por hora

IDEAM_CATALOGO_ID = os.getenv("IDEAM_CATALOGO_ID", "hp9r-jxuu")
# Catálogo Nacional de Estaciones IDEAM: lookup para código DANE por municipio

# ── Base de datos ───────────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://kwesx:kwesx2026@localhost:5432/kwesx_db",
)
DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg2://kwesx:kwesx2026@localhost:5432/kwesx_db",
)

# ── Parámetros ETL ──────────────────────────────────────────────────────────
BATCH_SIZE = int(os.getenv("ETL_BATCH_SIZE", "10000"))
# Socrata permite máximo 50,000 por request; usamos 10,000 para ser seguros.

FECHA_INICIO = os.getenv("ETL_FECHA_INICIO", "2021-01-01")
FECHA_FIN = os.getenv("ETL_FECHA_FIN", "2026-06-30")

# ── Columnas del Modelo Territorial Unificado (MTU) ─────────────────────────
# Estas son las columnas "compartidas" que todos los datasets deben tener
# después de la normalización. Documentadas aquí para referencia.
MTU_COLS = [
    "codigo_dane",    # 5 dígitos DIVIPOLA (NULL para datos nacionales como UPRA)
    "departamento",   # nombre del departamento
    "municipio",      # nombre del municipio
    "latitud",        # coordenada decimal
    "longitud",       # coordenada decimal
    "fecha",          # fecha de la observación (DATE)
    "sector",         # 'transporte' | 'agropecuario' | 'climatico'
    "fuente",         # 'ANI' | 'UPRA' | 'IDEAM'
]
