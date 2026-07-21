"""
backend/app/routers/datos.py
=============================
Router /datos — Endpoints para consultar los datos del MTU.

Endpoints
---------
GET /datos/ani                  — Tráfico vehicular en peajes
GET /datos/ani/{codigo_dane}    — Tráfico filtrado por municipio (DANE)
GET /datos/upra                 — Índice de precios de insumos agrícolas
GET /datos/upra/tendencia       — Serie temporal con variación mensual
GET /datos/ideam                — Variables climáticas (últimos N días)
GET /datos/ideam/{codigo_dane}  — Clima filtrado por municipio (DANE)
GET /datos/resumen              — Conteo de registros por fuente (salud del MTU)
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from datetime import date, timedelta
from typing import Optional

from backend.app.database import get_db
from backend.app.models.mtu import MtuANI, MtuUPRA, MtuIDEAM, MtuConectividad, MtuEducacion

router = APIRouter(prefix="/datos", tags=["Datos MTU"])


# ─────────────────────────────────────────────────────────────────────────────
# ANI — Tráfico vehicular
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/ani", summary="Tráfico vehicular en peajes (ANI)")
async def get_ani(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros a retornar"),
    desde: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    hasta: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    departamento: Optional[str] = Query(None, description="Filtrar por departamento"),
):
    """
    Retorna registros de tráfico vehicular en peajes nacionales.

    Fuente: ANI — Red de Peajes Concesionados.
    """
    query = select(MtuANI)

    if desde:
        query = query.where(MtuANI.fecha_inicio >= date.fromisoformat(desde))
    if hasta:
        query = query.where(MtuANI.fecha_fin <= date.fromisoformat(hasta))
    if departamento:
        query = query.where(MtuANI.departamento.ilike(f"%{departamento}%"))

    query = query.order_by(desc(MtuANI.fecha_inicio)).limit(limit)

    result = await db.execute(query)
    rows = result.scalars().all()
    return {"total": len(rows), "datos": [_ani_to_dict(r) for r in rows]}


@router.get("/ani/{codigo_dane}", summary="Tráfico vehicular por municipio")
async def get_ani_by_dane(
    codigo_dane: str,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=500),
):
    """Retorna tráfico vehicular para los peajes de un municipio (código DANE)."""
    query = (
        select(MtuANI)
        .where(MtuANI.codigo_dane == codigo_dane)
        .order_by(desc(MtuANI.fecha_inicio))
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No hay datos ANI para el código DANE '{codigo_dane}'.",
        )
    return {"codigo_dane": codigo_dane, "total": len(rows), "datos": [_ani_to_dict(r) for r in rows]}


# ─────────────────────────────────────────────────────────────────────────────
# UPRA — Índice de precios
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/upra", summary="Índice de precios de insumos agrícolas (UPRA)")
async def get_upra(
    db: AsyncSession = Depends(get_db),
    desde: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    hasta: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
):
    """
    Retorna la serie temporal mensual del índice de precios de insumos agrícolas.

    Fuente: UPRA — Índice de Precios de Insumos Agrícolas.
    Cobertura geográfica: Nacional.
    """
    query = select(MtuUPRA)

    if desde:
        query = query.where(MtuUPRA.fecha >= date.fromisoformat(desde))
    if hasta:
        query = query.where(MtuUPRA.fecha <= date.fromisoformat(hasta))

    query = query.order_by(MtuUPRA.fecha)
    result = await db.execute(query)
    rows = result.scalars().all()
    return {"total": len(rows), "datos": [_upra_to_dict(r) for r in rows]}


@router.get("/upra/tendencia", summary="Tendencia y variación mensual del índice UPRA")
async def get_upra_tendencia(db: AsyncSession = Depends(get_db)):
    """
    Retorna la serie completa con la variación mensual (delta) calculada.
    Útil para graficar la tendencia de precios en el dashboard.
    """
    query = select(MtuUPRA).order_by(MtuUPRA.fecha)
    result = await db.execute(query)
    rows = result.scalars().all()

    datos = []
    prev = None
    for r in rows:
        item = _upra_to_dict(r)
        if prev and prev["indice_total"] and r.indice_total:
            item["variacion_mensual_pct"] = round(
                ((r.indice_total - prev["indice_total"]) / prev["indice_total"]) * 100, 2
            )
        else:
            item["variacion_mensual_pct"] = None
        datos.append(item)
        prev = item

    return {"total": len(datos), "datos": datos}


# ─────────────────────────────────────────────────────────────────────────────
# IDEAM — Variables climáticas
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/ideam", summary="Variables climáticas por estación (IDEAM)")
async def get_ideam(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(200, ge=1, le=2000),
    dias: int = Query(7, ge=1, le=365, description="Últimos N días"),
    tipo: Optional[str] = Query(
        None,
        description="'precipitacion_mm' | 'temperatura_c' | None (ambas)",
    ),
    departamento: Optional[str] = Query(None),
):
    """
    Retorna mediciones climáticas de la red de estaciones IDEAM.

    Por defecto: últimos 7 días, todas las variables.
    """
    fecha_inicio = date.today() - timedelta(days=dias)

    query = select(MtuIDEAM).where(MtuIDEAM.fecha >= fecha_inicio)

    if tipo:
        query = query.where(MtuIDEAM.tipo_variable == tipo)
    if departamento:
        query = query.where(MtuIDEAM.departamento.ilike(f"%{departamento}%"))

    query = query.order_by(desc(MtuIDEAM.fecha)).limit(limit)

    result = await db.execute(query)
    rows = result.scalars().all()
    return {"total": len(rows), "datos": [_ideam_to_dict(r) for r in rows]}


@router.get("/ideam/{codigo_dane}", summary="Clima por municipio")
async def get_ideam_by_dane(
    codigo_dane: str,
    db: AsyncSession = Depends(get_db),
    dias: int = Query(30, ge=1, le=365),
    tipo: Optional[str] = Query(None),
):
    """Retorna variables climáticas para un municipio dado (código DANE)."""
    fecha_inicio = date.today() - timedelta(days=dias)

    query = select(MtuIDEAM).where(
        and_(
            MtuIDEAM.codigo_dane == codigo_dane,
            MtuIDEAM.fecha >= fecha_inicio,
        )
    )
    if tipo:
        query = query.where(MtuIDEAM.tipo_variable == tipo)

    query = query.order_by(desc(MtuIDEAM.fecha)).limit(500)
    result = await db.execute(query)
    rows = result.scalars().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No hay datos IDEAM para el código DANE '{codigo_dane}'.",
        )
    return {"codigo_dane": codigo_dane, "total": len(rows), "datos": [_ideam_to_dict(r) for r in rows]}


# ─────────────────────────────────────────────────────────────────────────────
# Resumen / salud del MTU
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/resumen", summary="Conteo de registros por fuente en el MTU")
async def get_resumen(db: AsyncSession = Depends(get_db)):
    """
    Retorna el estado actual del MTU: cuántos registros hay por tabla.
    Útil para verificar que el ETL se ejecutó correctamente.
    """
    ani_count          = await db.scalar(select(func.count()).select_from(MtuANI))
    upra_count         = await db.scalar(select(func.count()).select_from(MtuUPRA))
    ideam_count        = await db.scalar(select(func.count()).select_from(MtuIDEAM))
    conectividad_count = await db.scalar(select(func.count()).select_from(MtuConectividad))
    educacion_count    = await db.scalar(select(func.count()).select_from(MtuEducacion))

    # Rango de fechas IDEAM
    ideam_min = await db.scalar(select(func.min(MtuIDEAM.fecha)))
    ideam_max = await db.scalar(select(func.max(MtuIDEAM.fecha)))

    total = (ani_count or 0) + (upra_count or 0) + (ideam_count or 0) + \
            (conectividad_count or 0) + (educacion_count or 0)

    return {
        "total_registros": total,
        "mtu": {
            "ani":          {"registros": ani_count,          "tabla": "mtu_ani"},
            "upra":         {"registros": upra_count,          "tabla": "mtu_upra"},
            "ideam":        {"registros": ideam_count,         "tabla": "mtu_ideam",
                             "fecha_min": str(ideam_min), "fecha_max": str(ideam_max)},
            "conectividad": {"registros": conectividad_count,  "tabla": "mtu_conectividad"},
            "educacion":    {"registros": educacion_count,     "tabla": "mtu_educacion"},
        },
        "fuentes": ["ANI", "UPRA", "IDEAM", "DANE-MinTIC", "MEN-SIMAT"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de serialización
# ─────────────────────────────────────────────────────────────────────────────

def _ani_to_dict(r: MtuANI) -> dict:
    return {
        "id": r.id, "codigo_dane": r.codigo_dane, "departamento": r.departamento,
        "municipio": r.municipio, "latitud": r.latitud, "longitud": r.longitud,
        "peaje": r.peaje, "categoria_tarifa": r.categoria_tarifa,
        "fecha_inicio": str(r.fecha_inicio), "fecha_fin": str(r.fecha_fin),
        "valor_tarifa": r.valor_tarifa, "cantidad_trafico": r.cantidad_trafico,
        "cantidad_evasores": r.cantidad_evasores, "cantidad_exentos": r.cantidad_exentos,
        "fuente": r.fuente,
    }

def _upra_to_dict(r: MtuUPRA) -> dict:
    return {
        "id": r.id, "fecha": str(r.fecha),
        "indice_total": r.indice_total,
        "total_fertilizantes": r.total_fertilizantes,
        "total_plaguicidas": r.total_plaguicidas,
        "total_otros": r.total_otros,
        "fuente": r.fuente,
    }

def _ideam_to_dict(r: MtuIDEAM) -> dict:
    return {
        "id": r.id, "codigo_dane": r.codigo_dane, "departamento": r.departamento,
        "municipio": r.municipio, "latitud": r.latitud, "longitud": r.longitud,
        "fecha": str(r.fecha), "codigo_estacion": r.codigo_estacion,
        "nombre_estacion": r.nombre_estacion, "tipo_variable": r.tipo_variable,
        "valor_observado": r.valor_observado, "unidad_medida": r.unidad_medida,
        "zona_hidrografica": r.zona_hidrografica, "fuente": r.fuente,
    }


# -----------------------------------------------------------------------------
# Conectividad (DANE + MinTIC)
# -----------------------------------------------------------------------------

@router.get("/conectividad", summary="Brecha digital por municipio (DANE + MinTIC)")
async def get_conectividad(
    db: AsyncSession = Depends(get_db),
    departamento: Optional[str] = Query(None, description="Filtrar por departamento"),
    anio: Optional[int] = Query(None, description="Filtrar por ano (ej. 2023)"),
    zona: Optional[str] = Query(None, description="'urbana' | 'rural' | 'total'"),
    limit: int = Query(200, ge=1, le=2000),
):
    """
    Retorna datos de conectividad a internet por municipio.
    Fuente: DANE ECV + MinTIC Indice de Penetracion.
    """
    query = select(MtuConectividad)
    if departamento:
        query = query.where(MtuConectividad.departamento.ilike(f"%{departamento}%"))
    if anio:
        query = query.where(MtuConectividad.anio == anio)
    if zona:
        query = query.where(MtuConectividad.zona == zona)
    query = query.order_by(desc(MtuConectividad.pct_hogares_internet)).limit(limit)

    result = await db.execute(query)
    rows = result.scalars().all()
    return {"total": len(rows), "datos": [_conectividad_to_dict(r) for r in rows]}


# -----------------------------------------------------------------------------
# Educacion (MEN SIMAT)
# -----------------------------------------------------------------------------

@router.get("/educacion", summary="Cobertura educativa por municipio (MEN-SIMAT)")
async def get_educacion(
    db: AsyncSession = Depends(get_db),
    departamento: Optional[str] = Query(None, description="Filtrar por departamento"),
    nivel: Optional[str] = Query(None, description="'preescolar' | 'primaria' | 'secundaria' | 'media'"),
    anio: Optional[int] = Query(None, description="Filtrar por ano"),
    limit: int = Query(200, ge=1, le=2000),
):
    """
    Retorna tasas de cobertura educativa por municipio y nivel.
    Fuente: MEN -- SIMAT (Sistema Integrado de Matricula).
    """
    query = select(MtuEducacion)
    if departamento:
        query = query.where(MtuEducacion.departamento.ilike(f"%{departamento}%"))
    if nivel:
        query = query.where(MtuEducacion.nivel_educativo == nivel)
    if anio:
        query = query.where(MtuEducacion.anio == anio)
    query = query.order_by(MtuEducacion.departamento, MtuEducacion.municipio).limit(limit)

    result = await db.execute(query)
    rows = result.scalars().all()
    return {"total": len(rows), "datos": [_educacion_to_dict(r) for r in rows]}


# -----------------------------------------------------------------------------
# Helpers adicionales
# -----------------------------------------------------------------------------

def _conectividad_to_dict(r: MtuConectividad) -> dict:
    return {
        "id": r.id, "codigo_dane": r.codigo_dane,
        "departamento": r.departamento, "municipio": r.municipio,
        "anio": r.anio,
        "pct_hogares_internet": r.pct_hogares_internet,
        "pct_hogares_celular": r.pct_hogares_celular,
        "pct_hogares_pc": r.pct_hogares_pc,
        "tipo_conexion": r.tipo_conexion,
        "velocidad_mbps": r.velocidad_mbps,
        "zona": r.zona,
        "fuente": r.fuente,
    }

def _educacion_to_dict(r: MtuEducacion) -> dict:
    return {
        "id": r.id, "codigo_dane": r.codigo_dane,
        "departamento": r.departamento, "municipio": r.municipio,
        "anio": r.anio, "nivel_educativo": r.nivel_educativo,
        "matriculados": r.matriculados,
        "tasa_cobertura_neta": r.tasa_cobertura_neta,
        "tasa_cobertura_bruta": r.tasa_cobertura_bruta,
        "tasa_aprobacion": r.tasa_aprobacion,
        "tasa_desercion": r.tasa_desercion,
        "zona": r.zona,
        "fuente": r.fuente,
    }
