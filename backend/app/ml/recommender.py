"""
backend/app/ml/recommender.py
================================
Sistema de Recomendaciones Territoriales de Kwesx AI.

Genera recomendaciones de acción basadas en los datos más recientes del MTU:
  - UPRA  → precios de insumos agrícolas
  - IDEAM → variables climáticas
  - ANI   → tráfico vehicular en peajes
  - IVT   → índice de vulnerabilidad territorial (si el modelo está entrenado)

Las recomendaciones se priorizan según severidad y cruzan variables
para detectar situaciones compuestas (ej: precio alto + lluvia baja = riesgo agrícola).

Uso
---
from backend.app.ml.recommender import generar_recomendaciones
recs = await generar_recomendaciones(db)
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from backend.app.models.mtu import MtuANI, MtuUPRA, MtuIDEAM


# ─── Tipos ───────────────────────────────────────────────────────────────────

class Recomendacion(TypedDict):
    tipo:        str           # "precio" | "clima" | "trafico" | "riesgo_compuesto"
    titulo:      str
    descripcion: str
    acciones:    list[str]
    prioridad:   str           # "ALTA" | "MEDIA" | "BAJA"
    datos_base:  dict          # valores que motivaron la recomendación


# ─── Umbrales de alerta ───────────────────────────────────────────────────────

UMBRAL_PRECIO_FERTILIZANTE_ALTO  = 130.0   # índice UPRA fertilizantes
UMBRAL_PRECIO_TOTAL_ALTO         = 120.0   # índice UPRA total
UMBRAL_VARIACION_MENSUAL_ALTA    = 5.0     # % variación intermensal alta
UMBRAL_PRECIPITACION_BAJA        = 5.0     # mm promedio (posible sequía)
UMBRAL_PRECIPITACION_ALTA        = 150.0   # mm promedio (posible inundación)
UMBRAL_TEMPERATURA_ALTA          = 30.0    # °C promedio
UMBRAL_EVASION_ALTA              = 15.0    # % evasión en peajes


# ─── Función principal ────────────────────────────────────────────────────────

async def generar_recomendaciones(
    db: AsyncSession,
    municipio: str | None = None,
    departamento: str | None = None,
) -> list[Recomendacion]:
    """
    Consulta el estado actual del MTU y genera una lista priorizada
    de recomendaciones de acción territorial.
    """
    recs: list[Recomendacion] = []

    # 1. Analizar precios UPRA
    upra_rec = await _analizar_upra(db)
    if upra_rec:
        recs.extend(upra_rec)

    # 2. Analizar clima IDEAM
    clima_rec = await _analizar_clima(db, departamento)
    if clima_rec:
        recs.extend(clima_rec)

    # 3. Analizar tráfico ANI
    ani_rec = await _analizar_ani(db, departamento)
    if ani_rec:
        recs.extend(ani_rec)

    # 4. Detectar situaciones compuestas (cruce de variables)
    if recs:
        compuesto = _detectar_riesgo_compuesto(recs)
        if compuesto:
            recs.insert(0, compuesto)  # riesgo compuesto siempre primero

    # Si no hay alertas, generar recomendaciones de monitoreo estándar
    if not recs:
        recs = _recomendaciones_estandar()

    # Ordenar: ALTA → MEDIA → BAJA
    orden = {"ALTA": 0, "MEDIA": 1, "BAJA": 2}
    recs.sort(key=lambda r: orden.get(r["prioridad"], 3))

    return recs[:8]  # máximo 8 recomendaciones por consulta


# ─── Analizadores por fuente ──────────────────────────────────────────────────

async def _analizar_upra(db: AsyncSession) -> list[Recomendacion]:
    """Detecta alertas en precios de insumos agrícolas."""
    recs = []

    # Últimos 2 meses
    query = select(MtuUPRA).order_by(desc(MtuUPRA.fecha)).limit(2)
    result = await db.execute(query)
    rows = result.scalars().all()

    if not rows:
        return []

    ultimo = rows[0]
    anterior = rows[1] if len(rows) > 1 else None

    indice = float(ultimo.indice_total or 0)
    fertilizantes = float(ultimo.total_fertilizantes or 0)

    # Variación intermensal
    variacion_pct = 0.0
    if anterior and anterior.indice_total:
        variacion_pct = ((indice - float(anterior.indice_total)) / float(anterior.indice_total)) * 100

    # Alerta: fertilizantes altos
    if fertilizantes > UMBRAL_PRECIO_FERTILIZANTE_ALTO:
        recs.append(Recomendacion(
            tipo="precio",
            titulo="Fertilizantes con precio elevado",
            descripcion=(
                f"El índice de fertilizantes está en {fertilizantes:.1f}, "
                f"por encima del umbral de alerta ({UMBRAL_PRECIO_FERTILIZANTE_ALTO}). "
                "Esto puede aumentar los costos de producción agrícola."
            ),
            acciones=[
                "Considerar compra anticipada antes de nuevos incrementos.",
                "Explorar bioinsumos y fertilizantes orgánicos como alternativa.",
                "Consultar subsidios del Ministerio de Agricultura.",
                "Revisar el programa 'Fertilizantes para la Paz' del Gobierno.",
            ],
            prioridad="ALTA" if fertilizantes > UMBRAL_PRECIO_FERTILIZANTE_ALTO * 1.15 else "MEDIA",
            datos_base={
                "indice_fertilizantes": fertilizantes,
                "umbral": UMBRAL_PRECIO_FERTILIZANTE_ALTO,
                "fecha": str(ultimo.fecha),
            },
        ))

    # Alerta: variación mensual alta
    if abs(variacion_pct) > UMBRAL_VARIACION_MENSUAL_ALTA:
        direccion = "aumento" if variacion_pct > 0 else "caída"
        recs.append(Recomendacion(
            tipo="precio",
            titulo=f"Variación mensual significativa en insumos ({direccion})",
            descripcion=(
                f"El índice total de insumos agrícolas varió un {variacion_pct:+.1f}% "
                f"respecto al mes anterior. Una {direccion} de esta magnitud "
                "puede afectar la planificación de costos de los agricultores."
            ),
            acciones=[
                "Revisar contratos de suministro con proveedores.",
                "Ajustar el presupuesto de la próxima siembra.",
                "Consultar con la Unidad de Planificación Rural Agropecuaria (UPRA).",
            ],
            prioridad="MEDIA",
            datos_base={
                "variacion_pct": round(variacion_pct, 2),
                "indice_actual": indice,
                "indice_anterior": float(anterior.indice_total) if anterior else None,
            },
        ))

    return recs


async def _analizar_clima(
    db: AsyncSession,
    departamento: str | None,
) -> list[Recomendacion]:
    """Detecta alertas climáticas en los últimos 7 días."""
    recs = []
    fecha_inicio = date.today() - timedelta(days=7)

    query = (
        select(
            MtuIDEAM.tipo_variable,
            func.avg(MtuIDEAM.valor_observado).label("promedio"),
            func.max(MtuIDEAM.valor_observado).label("maximo"),
            func.count(MtuIDEAM.id).label("mediciones"),
        )
        .where(MtuIDEAM.fecha >= fecha_inicio)
    )
    if departamento:
        query = query.where(MtuIDEAM.departamento.ilike(f"%{departamento}%"))
    query = query.group_by(MtuIDEAM.tipo_variable)

    result = await db.execute(query)
    rows = result.all()

    for row in rows:
        promedio = float(row.promedio or 0)
        maximo   = float(row.maximo or 0)

        if row.tipo_variable == "precipitacion_mm":
            if promedio < UMBRAL_PRECIPITACION_BAJA and maximo < 10:
                recs.append(Recomendacion(
                    tipo="clima",
                    titulo="Posible condición de sequía",
                    descripcion=(
                        f"La precipitación promedio de los últimos 7 días es de "
                        f"{promedio:.1f} mm, con un máximo de {maximo:.1f} mm. "
                        "Esto puede indicar una condición seca que afecte cultivos."
                    ),
                    acciones=[
                        "Activar sistemas de riego suplementario.",
                        "Monitorear reservorios de agua en la zona.",
                        "Consultar el boletín de amenaza por sequía del IDEAM.",
                        "Priorizar cultivos con mayor resistencia a la sequía.",
                    ],
                    prioridad="ALTA",
                    datos_base={
                        "precipitacion_promedio_mm": round(promedio, 2),
                        "precipitacion_maxima_mm": round(maximo, 2),
                        "umbral_sequia": UMBRAL_PRECIPITACION_BAJA,
                    },
                ))
            elif promedio > UMBRAL_PRECIPITACION_ALTA:
                recs.append(Recomendacion(
                    tipo="clima",
                    titulo="Precipitaciones intensas — riesgo de inundación",
                    descripcion=(
                        f"La precipitación promedio de {promedio:.1f} mm en los últimos "
                        f"7 días supera el umbral de alerta ({UMBRAL_PRECIPITACION_ALTA} mm). "
                        "Pueden presentarse deslizamientos o inundaciones."
                    ),
                    acciones=[
                        "Revisar el estado de drenajes y canales de agua.",
                        "Consultar las alertas tempranas del SGC y UNGRD.",
                        "Verificar accesibilidad de vías rurales con ANI.",
                        "Proteger cultivos susceptibles a encharcamiento.",
                    ],
                    prioridad="ALTA",
                    datos_base={
                        "precipitacion_promedio_mm": round(promedio, 2),
                        "precipitacion_maxima_mm": round(maximo, 2),
                        "umbral_inundacion": UMBRAL_PRECIPITACION_ALTA,
                    },
                ))

        elif row.tipo_variable == "temperatura_c":
            if promedio > UMBRAL_TEMPERATURA_ALTA:
                recs.append(Recomendacion(
                    tipo="clima",
                    titulo="Temperatura elevada — estrés térmico en cultivos",
                    descripcion=(
                        f"La temperatura promedio de {promedio:.1f}°C en los últimos "
                        f"7 días supera el umbral ({UMBRAL_TEMPERATURA_ALTA}°C). "
                        "Esto puede causar estrés hídrico y reducir rendimientos."
                    ),
                    acciones=[
                        "Aumentar frecuencia de riego en cultivos sensibles.",
                        "Aplicar coberturas vegetales o mulching.",
                        "Ajustar horarios de fumigación a horas más frescas.",
                        "Revisar disponibilidad de agua en acuíferos locales.",
                    ],
                    prioridad="MEDIA",
                    datos_base={
                        "temperatura_promedio_c": round(promedio, 2),
                        "temperatura_maxima_c": round(maximo, 2),
                        "umbral": UMBRAL_TEMPERATURA_ALTA,
                    },
                ))

    return recs


async def _analizar_ani(
    db: AsyncSession,
    departamento: str | None,
) -> list[Recomendacion]:
    """Detecta alertas de evasión o saturación en peajes ANI."""
    recs = []

    query = select(
        func.sum(MtuANI.cantidad_trafico).label("trafico"),
        func.sum(MtuANI.cantidad_evasores).label("evasores"),
        func.count(MtuANI.id).label("periodos"),
    )
    if departamento:
        query = query.where(MtuANI.departamento.ilike(f"%{departamento}%"))

    result = await db.execute(query)
    row = result.first()

    trafico  = int(row.trafico  or 0)
    evasores = int(row.evasores or 0)
    if trafico == 0:
        return []

    pct_evasion = (evasores / trafico) * 100

    if pct_evasion > UMBRAL_EVASION_ALTA:
        recs.append(Recomendacion(
            tipo="trafico",
            titulo="Tasa de evasión en peajes por encima del umbral",
            descripcion=(
                f"Se registra una tasa de evasión de {pct_evasion:.1f}% en la red de peajes "
                f"({evasores:,} evasores de {trafico:,} vehículos totales). "
                "Una tasa superior al 15% impacta el recaudo para mantenimiento vial."
            ),
            acciones=[
                "Revisar el estado de las cabinas y sistemas de cobro electrónico.",
                "Coordinar con la ANI para auditoría de puntos de evasión frecuente.",
                "Evaluar mejoras en señalización en tramos con alta evasión.",
            ],
            prioridad="MEDIA",
            datos_base={
                "trafico_total": trafico,
                "evasores": evasores,
                "pct_evasion": round(pct_evasion, 2),
                "umbral": UMBRAL_EVASION_ALTA,
            },
        ))

    return recs


# ─── Detección de riesgos compuestos ─────────────────────────────────────────

def _detectar_riesgo_compuesto(recs: list[Recomendacion]) -> Recomendacion | None:
    """
    Si hay alertas simultáneas de precio + clima, genera una recomendación
    de riesgo compuesto con prioridad ALTA.
    """
    tipos = {r["tipo"] for r in recs}
    tiene_precio = "precio" in tipos
    tiene_clima  = "clima"  in tipos

    if tiene_precio and tiene_clima:
        alta_prioridad = any(r["prioridad"] == "ALTA" for r in recs)
        return Recomendacion(
            tipo="riesgo_compuesto",
            titulo="Alerta compuesta: presión agrícola simultánea",
            descripcion=(
                "Se detectan simultáneamente alertas de precios de insumos y condiciones "
                "climáticas adversas. Esta combinación puede reducir significativamente "
                "la rentabilidad del sector agrícola territorial."
            ),
            acciones=[
                "Activar mesa de trabajo interinstitucional (UPRA + IDEAM + Min. Agricultura).",
                "Revisar los mecanismos de seguro agropecuario disponibles.",
                "Priorizar asistencia técnica a pequeños productores.",
                "Evaluar declaración de calamidad si la situación escala.",
            ],
            prioridad="ALTA" if alta_prioridad else "MEDIA",
            datos_base={
                "alertas_activas": [r["titulo"] for r in recs],
                "tipos_detectados": list(tipos),
            },
        )
    return None


# ─── Recomendaciones estándar (sin alertas activas) ──────────────────────────

def _recomendaciones_estandar() -> list[Recomendacion]:
    """Recomendaciones de monitoreo cuando no hay alertas activas."""
    return [
        Recomendacion(
            tipo="precio",
            titulo="Monitoreo periódico de precios agrícolas",
            descripcion=(
                "Los precios de insumos agrícolas se encuentran dentro de rangos normales. "
                "Se recomienda monitoreo continuo mensual."
            ),
            acciones=[
                "Revisar el boletín mensual UPRA.",
                "Comparar precios locales con el índice nacional.",
            ],
            prioridad="BAJA",
            datos_base={"estado": "normal"},
        ),
        Recomendacion(
            tipo="clima",
            titulo="Condiciones climáticas estables",
            descripcion=(
                "Las variables climáticas del IDEAM no muestran anomalías significativas. "
                "Buen momento para planificación de siembras."
            ),
            acciones=[
                "Consultar el calendario agroclimático del IDEAM.",
                "Planificar siembras según el ciclo climático proyectado.",
            ],
            prioridad="BAJA",
            datos_base={"estado": "normal"},
        ),
    ]
