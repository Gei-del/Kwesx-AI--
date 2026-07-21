"""
backend/app/routers/asistente.py
=================================
Router /asistente — Asistente conversacional de Kwesx AI.

Implementa el Asistente Inteligente Territorial (AIT) con reconocimiento
de intención basado en palabras clave + plantillas de respuesta.

Esta es la versión MVP (v1): sin LLM externo, sin NLP pesado.
El asistente interpreta preguntas en español sobre los datos del MTU
y retorna una respuesta estructurada + datos de soporte.

Endpoints
---------
POST /asistente/chat            — Enviar mensaje y recibir respuesta
GET  /asistente/ejemplos        — Ver preguntas de ejemplo
GET  /asistente/estado          — Estado del asistente y capacidades

Intenciones soportadas (v1)
----------------------------
- "tráfico"/"peaje"/"vehículos" → consulta ANI por departamento/período
- "precio"/"insumo"/"fertilizante"/"plaguicida" → tendencia UPRA
- "lluvia"/"precipitación"/"temperatura"/"clima" → datos IDEAM por zona
- "resumen"/"estado"/"cuántos" → resumen del MTU
- "ayuda"/"¿qué puedes?" → guía de uso
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from datetime import date, timedelta
import re

from backend.app.database import get_db
from backend.app.models.mtu import MtuANI, MtuUPRA, MtuIDEAM
from backend.app.ml.nlp_intent import clasificar_intencion

router = APIRouter(prefix="/asistente", tags=["Asistente IA"])


# ─────────────────────────────────────────────────────────────────────────────
# Modelos de entrada/salida
# ─────────────────────────────────────────────────────────────────────────────

class MensajeRequest(BaseModel):
    texto: str
    contexto: dict = {}   # historial simplificado o filtros activos

class AsistenteResponse(BaseModel):
    intencion: str
    respuesta: str
    datos: dict = {}
    sugerencias: list[str] = []
    confianza: float = 0.0   # score NLP 0–1


# ─────────────────────────────────────────────────────────────────────────────
# Motor de reconocimiento de intención (keyword-based, MVP)
# ─────────────────────────────────────────────────────────────────────────────


def extraer_departamento(texto: str) -> str | None:
    """Extrae nombre de departamento del texto si aparece alguno conocido."""
    DEPARTAMENTOS = [
        "antioquia", "cundinamarca", "valle", "atlántico", "atlantico",
        "bolívar", "bolivar", "santander", "nariño", "narino", "cauca",
        "tolima", "huila", "boyacá", "boyaca", "caldas", "risaralda",
        "quindío", "quindio", "meta", "cesar", "magdalena", "córdoba",
        "cordoba", "sucre", "guajira", "chocó", "choco", "casanare",
    ]
    texto_lower = texto.lower()
    for d in DEPARTAMENTOS:
        if d in texto_lower:
            return d.capitalize()
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=AsistenteResponse, summary="Chatear con el asistente")
async def chat(req: MensajeRequest, db: AsyncSession = Depends(get_db)):
    """
    Procesa un mensaje en lenguaje natural y retorna una respuesta
    con datos de soporte del MTU.
    """
    # ── NLP: clasificar intención con TF-IDF + cosine (fallback: keyword) ──
    nlp_result   = clasificar_intencion(req.texto)
    intencion    = nlp_result.intencion
    confianza    = nlp_result.confianza
    departamento = extraer_departamento(req.texto)

    if intencion == "trafico":
        resp = await _responder_trafico(db, req.texto, departamento)
    elif intencion == "precios":
        resp = await _responder_precios(db)
    elif intencion == "clima":
        resp = await _responder_clima(db, departamento)
    elif intencion == "resumen":
        resp = await _responder_resumen(db)
    elif intencion == "ayuda":
        resp = _responder_ayuda()
    elif intencion == "ivt":
        resp = AsistenteResponse(
            intencion="ivt",
            respuesta=(
                "El Índice de Vulnerabilidad Territorial (IVT) combina datos de precios "
                "agrícolas (UPRA), clima (IDEAM) y movilidad (ANI) para clasificar zonas "
                "en vulnerabilidad BAJA, MEDIA o ALTA. Consulta el panel **Predicción** "
                "para ver el resultado del modelo con tus datos más recientes."
            ),
            sugerencias=[
                "¿Cuál es el índice de precios este mes?",
                "¿Cuánta lluvia cayó recientemente?",
            ],
        )
    elif intencion == "anomalia":
        resp = AsistenteResponse(
            intencion="anomalia",
            respuesta=(
                "El sistema de detección de anomalías (Isolation Forest + LOF) monitorea "
                "continuamente las series de datos del MTU. Consulta el panel **Insights de IA** "
                "para ver las últimas alertas y los scores de anomalía por período."
            ),
            sugerencias=[
                "¿Qué datos tienen el sistema actualmente?",
                "¿Cómo están los precios este mes?",
            ],
        )
    elif intencion == "forecast":
        resp = AsistenteResponse(
            intencion="forecast",
            respuesta=(
                "Las predicciones de series temporales (Holt-Winters + SARIMA) están disponibles "
                "en el panel **Insights de IA**, sección Forecasting. Muestran la tendencia "
                "proyectada a 6 meses con intervalos de confianza al 95%."
            ),
            sugerencias=[
                "¿Cómo están los precios actuales de insumos?",
                "¿Hay alguna alerta climática activa?",
            ],
        )
    else:
        resp = AsistenteResponse(
            intencion="desconocido",
            respuesta=(
                "No entendí bien tu pregunta. Puedo ayudarte con información sobre "
                "tráfico vehicular en peajes (ANI), precios de insumos agrícolas (UPRA), "
                "variables climáticas (IDEAM) o la predicción territorial (IVT). "
                "¿Sobre cuál tema quieres saber más?"
            ),
            sugerencias=[
                "¿Cuántos vehículos pasaron por peajes en Antioquia?",
                "¿Cómo han cambiado los precios de fertilizantes?",
                "¿Cuánta lluvia cayó en Bogotá esta semana?",
            ],
        )

    resp.confianza = confianza
    return resp


@router.get("/ejemplos", summary="Preguntas de ejemplo")
async def get_ejemplos():
    """Retorna preguntas de ejemplo para guiar al usuario."""
    return {
        "preguntas": [
            # Tráfico
            "¿Cuántos vehículos pasaron por los peajes de Antioquia el mes pasado?",
            "¿Cuál es el peaje con más evasiones en Colombia?",
            "¿Cómo ha variado el tráfico en los corredores viales del Valle?",
            # Precios
            "¿Cómo están los precios de insumos agrícolas en 2026?",
            "¿Han subido los fertilizantes este año?",
            "¿Cuál es la tendencia del índice de plaguicidas?",
            # Clima
            "¿Cuánta precipitación registró Medellín esta semana?",
            "¿Cuál es la temperatura promedio en Bogotá hoy?",
            "¿Hay alguna alerta climática en el Caribe colombiano?",
            # General
            "¿Cuántos datos tiene Kwesx AI actualmente?",
            "¿Qué puedes hacer?",
        ]
    }


@router.get("/estado", summary="Estado del asistente")
async def get_estado():
    """Retorna información sobre el estado y capacidades del asistente."""
    return {
        "version": "1.0.0-mvp",
        "tipo": "keyword-based",
        "descripcion": "Asistente Inteligente Territorial (AIT) — MVP v1",
        "intenciones_soportadas": list(INTENCIONES.keys()),
        "datasets_activos": ["ANI Tráfico Vehicular", "UPRA Insumos Agrícolas", "IDEAM Variables Climáticas"],
        "mejoras_planificadas": [
            "Integración con LLM para respuestas más naturales",
            "Reconocimiento de entidades geográficas más amplio",
            "Memoria de contexto multi-turno",
            "Alertas automáticas por umbrales climáticos",
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Funciones de respuesta por intención
# ─────────────────────────────────────────────────────────────────────────────

async def _responder_trafico(db, texto: str, departamento: str | None) -> AsistenteResponse:
    query = select(
        func.sum(MtuANI.cantidad_trafico).label("trafico_total"),
        func.sum(MtuANI.cantidad_evasores).label("evasores_total"),
        func.count(MtuANI.id).label("periodos"),
    )
    if departamento:
        query = query.where(MtuANI.departamento.ilike(f"%{departamento}%"))

    result = await db.execute(query)
    row = result.first()

    trafico = int(row.trafico_total or 0)
    evasores = int(row.evasores_total or 0)
    periodos = int(row.periodos or 0)
    pct_evasion = round((evasores / trafico * 100), 2) if trafico > 0 else 0

    zona = f"en {departamento}" if departamento else "en todos los departamentos"
    respuesta = (
        f"Según los datos ANI disponibles {zona}, hay un total de "
        f"**{trafico:,}** vehículos registrados en {periodos:,} períodos de medición. "
        f"Se registraron **{evasores:,}** evasiones "
        f"({pct_evasion}% del tráfico total). "
    )
    if pct_evasion > 10:
        respuesta += "⚠️ El porcentaje de evasión es significativo."

    return AsistenteResponse(
        intencion="trafico",
        respuesta=respuesta,
        datos={
            "trafico_total": trafico,
            "evasores_total": evasores,
            "periodos": periodos,
            "pct_evasion": pct_evasion,
            "filtro_departamento": departamento,
        },
        sugerencias=[
            "¿Cuál es el peaje con más tráfico?",
            "Muéstrame el tráfico por categoría vehicular.",
        ],
    )


async def _responder_precios(db) -> AsistenteResponse:
    # Últimas 6 filas (6 meses)
    query = select(MtuUPRA).order_by(desc(MtuUPRA.fecha)).limit(6)
    result = await db.execute(query)
    rows = result.scalars().all()
    rows = list(reversed(rows))  # orden cronológico

    if not rows:
        return AsistenteResponse(
            intencion="precios",
            respuesta=(
                "Los datos de precios agrícolas se están actualizando. "
                "Intenta de nuevo en unos minutos o consulta directamente en "
                "datos.gov.co/Agricultura-y-Desarrollo-Rural."
            ),
            sugerencias=[
                "¿Qué datos climáticos hay disponibles?",
                "¿Cuántos registros tiene el sistema ahora?",
            ],
        )

    ultimo = rows[-1]
    primero = rows[0]
    variacion = None
    if ultimo.indice_total and primero.indice_total:
        variacion = round(
            ((ultimo.indice_total - primero.indice_total) / primero.indice_total) * 100, 2
        )

    respuesta = (
        f"El índice nacional de precios de insumos agrícolas (UPRA) en "
        f"**{str(ultimo.fecha)[:7]}** es de **{ultimo.indice_total:.1f}**. "
    )
    if variacion is not None:
        direccion = "subió" if variacion > 0 else "bajó"
        respuesta += f"En los últimos 6 meses, el índice {direccion} un **{abs(variacion)}%**. "
    if ultimo.total_fertilizantes:
        respuesta += f"El subíndice de fertilizantes está en {ultimo.total_fertilizantes:.1f}."

    return AsistenteResponse(
        intencion="precios",
        respuesta=respuesta,
        datos={
            "ultimo_mes": str(ultimo.fecha),
            "indice_total": ultimo.indice_total,
            "fertilizantes": ultimo.total_fertilizantes,
            "plaguicidas": ultimo.total_plaguicidas,
            "variacion_6m_pct": variacion,
            "serie": [
                {"fecha": str(r.fecha), "indice": r.indice_total} for r in rows
            ],
        },
        sugerencias=[
            "¿Cómo están los fertilizantes específicamente?",
            "¿Cuál fue el mes con mayor aumento de precios?",
        ],
    )


async def _responder_clima(db, departamento: str | None) -> AsistenteResponse:
    fecha_inicio = date.today() - timedelta(days=7)

    query = select(
        MtuIDEAM.tipo_variable,
        func.avg(MtuIDEAM.valor_observado).label("promedio"),
        func.max(MtuIDEAM.valor_observado).label("maximo"),
        func.count(MtuIDEAM.id).label("mediciones"),
    ).where(MtuIDEAM.fecha >= fecha_inicio)

    if departamento:
        query = query.where(MtuIDEAM.departamento.ilike(f"%{departamento}%"))

    query = query.group_by(MtuIDEAM.tipo_variable)
    result = await db.execute(query)
    rows = result.all()

    if not rows:
        zona = f"en {departamento}" if departamento else "para el período consultado"
        return AsistenteResponse(
            intencion="clima",
            respuesta=(
                f"No encontré datos climáticos recientes {zona}. "
                "La información se actualiza periódicamente desde las estaciones del IDEAM. "
                "Intenta de nuevo en unos minutos o consulta en ideam.gov.co."
            ),
            sugerencias=[
                "¿Cómo están los precios de insumos agrícolas?",
                "¿Cuántos datos tiene el sistema en total?",
            ],
        )

    zona = f"en {departamento}" if departamento else "a nivel nacional"
    datos_resp = {}
    lineas = []

    for row in rows:
        if row.tipo_variable == "precipitacion_mm":
            lineas.append(
                f"🌧 Precipitación {zona}: promedio **{row.promedio:.1f} mm**, "
                f"máximo **{row.maximo:.1f} mm** ({row.mediciones:,} mediciones en 7 días)."
            )
            datos_resp["precipitacion"] = {
                "promedio_mm": round(row.promedio, 2),
                "maximo_mm": round(row.maximo, 2),
                "mediciones": row.mediciones,
            }
        elif row.tipo_variable == "temperatura_c":
            lineas.append(
                f"🌡 Temperatura {zona}: promedio **{row.promedio:.1f}°C**, "
                f"máximo **{row.maximo:.1f}°C** ({row.mediciones:,} mediciones en 7 días)."
            )
            datos_resp["temperatura"] = {
                "promedio_c": round(row.promedio, 2),
                "maximo_c": round(row.maximo, 2),
                "mediciones": row.mediciones,
            }

    respuesta = " ".join(lineas) if lineas else "No se encontraron datos climáticos."

    return AsistenteResponse(
        intencion="clima",
        respuesta=respuesta,
        datos=datos_resp,
        sugerencias=[
            "¿Cuál es la estación con más lluvia?",
            "¿Hay diferencias de temperatura entre regiones?",
        ],
    )


async def _responder_resumen(db) -> AsistenteResponse:
    ani_count   = await db.scalar(select(func.count()).select_from(MtuANI))
    upra_count  = await db.scalar(select(func.count()).select_from(MtuUPRA))
    ideam_count = await db.scalar(select(func.count()).select_from(MtuIDEAM))
    total = (ani_count or 0) + (upra_count or 0) + (ideam_count or 0)

    return AsistenteResponse(
        intencion="resumen",
        respuesta=(
            f"El Modelo Territorial Unificado (MTU) de Kwesx AI tiene actualmente "
            f"**{total:,}** registros en total: "
            f"{ani_count:,} de tráfico vehicular (ANI), "
            f"{upra_count:,} de precios agrícolas (UPRA) y "
            f"{ideam_count:,} de variables climáticas (IDEAM)."
        ),
        datos={
            "total": total,
            "ani": ani_count,
            "upra": upra_count,
            "ideam": ideam_count,
        },
    )


def _responder_ayuda() -> AsistenteResponse:
    return AsistenteResponse(
        intencion="ayuda",
        respuesta=(
            "Soy el Asistente Inteligente Territorial de **Kwesx AI**. "
            "Puedo responder preguntas sobre tres fuentes de datos del gobierno colombiano: "
            "(1) **ANI** — tráfico vehicular en peajes; "
            "(2) **UPRA** — precios de insumos agrícolas; "
            "(3) **IDEAM** — precipitación y temperatura. "
            "Solo pregúntame en español natural, por ejemplo: "
            "'¿Cuánta lluvia cayó en Medellín esta semana?'"
        ),
        sugerencias=[
            "¿Cuántos vehículos pasaron por los peajes de Antioquia?",
            "¿Cómo están los precios de fertilizantes en 2026?",
            "¿Cuál es la temperatura promedio en Bogotá?",
        ],
    )
