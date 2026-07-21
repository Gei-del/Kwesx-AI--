"""
backend/app/routers/salud.py
=============================
Router /salud — Health checks y monitoreo de la API.

Endpoints
---------
GET /salud          — Estado general de la API (liveness probe)
GET /salud/db       — Estado de la conexión a PostgreSQL (readiness probe)
GET /salud/etl      — Estado de los datos en el MTU (completitud)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime

from backend.app.database import get_db
from backend.app.models.mtu import MtuANI, MtuUPRA, MtuIDEAM
from backend.app.config import settings

router = APIRouter(prefix="/salud", tags=["Salud y Monitoreo"])


@router.get("", summary="Liveness probe — ¿está viva la API?")
async def health_check():
    """
    Retorna OK si la API está respondiendo.
    Úsalo como liveness probe en Docker/Kubernetes.
    """
    return {
        "status": "ok",
        "proyecto": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/db", summary="Readiness probe — ¿está conectada la BD?")
async def db_health(db: AsyncSession = Depends(get_db)):
    """
    Verifica que la conexión a PostgreSQL está activa.
    Úsalo como readiness probe.
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {
            "status": "ok",
            "database": "postgresql",
            "message": "Conexión exitosa a PostgreSQL + PostGIS.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "database": "postgresql",
            "message": str(exc),
        }


@router.get("/etl", summary="Estado del ETL y completitud del MTU")
async def etl_health(db: AsyncSession = Depends(get_db)):
    """
    Verifica que el ETL se ejecutó y hay datos en las 3 tablas del MTU.
    Retorna advertencias si alguna tabla está vacía.
    """
    ani_count   = await db.scalar(select(func.count()).select_from(MtuANI))
    upra_count  = await db.scalar(select(func.count()).select_from(MtuUPRA))
    ideam_count = await db.scalar(select(func.count()).select_from(MtuIDEAM))

    # Última fecha de carga en IDEAM
    ideam_max_fecha = await db.scalar(select(func.max(MtuIDEAM.fecha)))

    advertencias = []
    if not ani_count:
        advertencias.append("mtu_ani está vacía. Ejecuta: python -m etl.pipeline --fuente ani")
    if not upra_count:
        advertencias.append("mtu_upra está vacía. Ejecuta: python -m etl.pipeline --fuente upra")
    if not ideam_count:
        advertencias.append("mtu_ideam está vacía. Ejecuta: python -m etl.pipeline --fuente ideam")

    status = "ok" if not advertencias else "warning"

    return {
        "status": status,
        "mtu": {
            "ani":   {"registros": ani_count,   "ok": bool(ani_count)},
            "upra":  {"registros": upra_count,   "ok": bool(upra_count)},
            "ideam": {"registros": ideam_count,  "ok": bool(ideam_count),
                      "ultima_fecha": str(ideam_max_fecha) if ideam_max_fecha else None},
        },
        "advertencias": advertencias,
        "timestamp": datetime.utcnow().isoformat(),
    }
