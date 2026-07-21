"""
backend/app/routers/recomendaciones.py
========================================
Router /recomendaciones — Sistema de Recomendaciones Territoriales.

Genera y retorna recomendaciones de acción basadas en el análisis cruzado
de datos UPRA, IDEAM y ANI. Las alertas se priorizan automáticamente.

Endpoints
---------
GET  /recomendaciones              — Recomendaciones para todo el territorio
GET  /recomendaciones?departamento=Antioquia — Filtradas por zona
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.app.database import get_db
from backend.app.ml.recommender import generar_recomendaciones

router = APIRouter(prefix="/recomendaciones", tags=["Recomendaciones IA"])


@router.get("/", summary="Recomendaciones territoriales priorizadas")
async def get_recomendaciones(
    departamento: Optional[str] = Query(None, description="Filtrar por departamento"),
    municipio:    Optional[str] = Query(None, description="Filtrar por municipio"),
    db: AsyncSession = Depends(get_db),
):
    """
    Genera recomendaciones de acción territorial basadas en el estado actual del MTU.

    Cruza datos de:
    - **UPRA**: Precios de insumos agrícolas
    - **IDEAM**: Variables climáticas (precipitación, temperatura)
    - **ANI**: Tráfico vehicular y evasión en peajes

    Retorna una lista priorizada (ALTA → MEDIA → BAJA) de hasta 8 recomendaciones.
    """
    recs = await generar_recomendaciones(
        db,
        municipio=municipio,
        departamento=departamento,
    )

    return {
        "total": len(recs),
        "zona": departamento or municipio or "Nacional",
        "recomendaciones": recs,
        "nota": (
            "Las recomendaciones se generan automáticamente cruzando los datos "
            "más recientes del MTU. No reemplazan el criterio técnico especializado."
        ),
    }
