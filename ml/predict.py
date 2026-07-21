"""
ml/predict.py
=============
Servicio de predicción del IVT — usado por la API FastAPI.

Carga el modelo una sola vez al iniciar la aplicación (singleton pattern)
y expone funciones de predicción para los endpoints.

Funciones principales
---------------------
get_modelo()         — retorna la instancia del modelo (lazy loading)
predecir_periodo()   — predice el IVT para un período dado
predecir_tendencia() — predice la tendencia del próximo mes
get_ivt_actual()     — calcula el IVT con los datos más recientes de la API
"""

import requests
from datetime import date, timedelta
from functools import lru_cache
from loguru import logger

from ml.modelo_territorial import ModeloTerritorial
from ml.features import build_prediction_features, NORMAL_PRECIPITACION_MM, NORMAL_TEMPERATURA_C
from etl.config import SOCRATA_BASE, SOCRATA_HEADERS, UPRA_DATASET_ID, IDEAM_PRECIPITACION_ID, IDEAM_TEMPERATURA_ID


# ─────────────────────────────────────────────────────────────────────────────
# Singleton del modelo
# ─────────────────────────────────────────────────────────────────────────────

_modelo_instance: ModeloTerritorial | None = None


def get_modelo() -> ModeloTerritorial | None:
    """
    Retorna la instancia del modelo (lazy loading).

    Si el modelo no está entrenado, retorna None y el endpoint
    indica que hay que ejecutar el entrenamiento.
    """
    global _modelo_instance
    if _modelo_instance is None:
        modelo = ModeloTerritorial()
        if modelo.is_trained():
            try:
                modelo.load()
                _modelo_instance = modelo
                logger.info("[Predict] Modelo IVT cargado exitosamente.")
            except Exception as e:
                logger.warning(f"[Predict] No se pudo cargar el modelo: {e}")
                return None
        else:
            logger.warning("[Predict] Modelo no entrenado. Ejecuta: python -m ml.train")
            return None
    return _modelo_instance


def reload_modelo() -> bool:
    """Fuerza recarga del modelo desde disco (útil después de reentrenar)."""
    global _modelo_instance
    _modelo_instance = None
    return get_modelo() is not None


# ─────────────────────────────────────────────────────────────────────────────
# Funciones de predicción
# ─────────────────────────────────────────────────────────────────────────────

def get_ivt_actual() -> dict:
    """
    Calcula el IVT para el período actual usando los últimos datos disponibles.

    Descarga:
    - Último mes UPRA disponible
    - Promedio de los últimos 30 días de IDEAM

    Returns
    -------
    dict con:
      - ivt: resultado de predicción (clase, etiqueta, probabilidades)
      - inputs: los valores usados como features
      - fecha_calculo: fecha en que se calculó
      - modelo_disponible: bool
    """
    modelo = get_modelo()
    if not modelo:
        return {
            "modelo_disponible": False,
            "mensaje": "Modelo no entrenado. Ejecuta primero: python -m ml.train",
        }

    # Obtener últimos datos UPRA
    upra = _fetch_ultimo_upra()
    # Obtener promedios IDEAM últimos 30 días
    clima = _fetch_clima_reciente(dias=30)

    # Construir features
    X = build_prediction_features(
        upra_indice=upra.get("indice_total", 115.0),
        upra_var_pct=upra.get("variacion_pct", 0.0),
        upra_fertilizantes=upra.get("total_fertilizantes", 120.0),
        upra_plaguicidas=upra.get("total_plaguicidas", 110.0),
        precipitacion_mm=clima.get("precipitacion_mm", NORMAL_PRECIPITACION_MM),
        temperatura_c=clima.get("temperatura_c", NORMAL_TEMPERATURA_C),
        fecha=date.today(),
    )

    resultado = modelo.predict(X)

    return {
        "modelo_disponible": True,
        "ivt": resultado,
        "inputs": {
            "upra_indice_total": upra.get("indice_total"),
            "upra_variacion_pct": upra.get("variacion_pct"),
            "precipitacion_mm": clima.get("precipitacion_mm"),
            "temperatura_c": clima.get("temperatura_c"),
            "fecha_upra": upra.get("fecha"),
            "periodo_clima_dias": 30,
        },
        "fecha_calculo": date.today().isoformat(),
        "interpretacion": _interpretar(resultado["etiqueta"], upra, clima),
    }


def predecir_desde_inputs(
    upra_indice: float,
    upra_var_pct: float,
    upra_fertilizantes: float,
    upra_plaguicidas: float,
    precipitacion_mm: float,
    temperatura_c: float,
    fecha: date = None,
) -> dict:
    """
    Predice el IVT dado un conjunto de valores de entrada explícitos.
    Útil para el endpoint que permite al usuario "jugar" con los parámetros.
    """
    if fecha is None:
        fecha = date.today()

    modelo = get_modelo()
    if not modelo:
        return {"modelo_disponible": False, "mensaje": "Modelo no entrenado."}

    X = build_prediction_features(
        upra_indice=upra_indice,
        upra_var_pct=upra_var_pct,
        upra_fertilizantes=upra_fertilizantes,
        upra_plaguicidas=upra_plaguicidas,
        precipitacion_mm=precipitacion_mm,
        temperatura_c=temperatura_c,
        fecha=fecha,
    )

    resultado = modelo.predict(X)
    return {
        "modelo_disponible": True,
        "ivt": resultado,
        "fecha": fecha.isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers — fetchers de datos actuales
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_ultimo_upra() -> dict:
    """Descarga el último registro UPRA disponible."""
    url = f"{SOCRATA_BASE}/{UPRA_DATASET_ID}.json"
    params = {
        "$select": "fecha, indice_total, total_fertilizantes, total_plaguicidas",
        "$order": "fecha DESC",
        "$limit": 2,
    }
    try:
        resp = requests.get(url, headers=SOCRATA_HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            return {}

        ultimo = rows[0]
        anterior = rows[1] if len(rows) > 1 else {}

        indice_actual = float(ultimo.get("indice_total", 0) or 0)
        indice_anterior = float(anterior.get("indice_total", indice_actual) or indice_actual)
        var_pct = ((indice_actual - indice_anterior) / indice_anterior * 100) if indice_anterior else 0

        return {
            "fecha": ultimo.get("fecha", "")[:10],
            "indice_total": indice_actual,
            "total_fertilizantes": float(ultimo.get("total_fertilizantes", 0) or 0),
            "total_plaguicidas": float(ultimo.get("total_plaguicidas", 0) or 0),
            "variacion_pct": round(var_pct, 3),
        }
    except Exception as e:
        logger.warning(f"[Predict] Error fetching UPRA: {e}")
        return {"indice_total": 115.0, "variacion_pct": 0.0,
                "total_fertilizantes": 120.0, "total_plaguicidas": 110.0}


def _fetch_clima_reciente(dias: int = 30) -> dict:
    """Descarga promedio de precipitación y temperatura de los últimos `dias` días."""
    fecha_inicio = (date.today() - timedelta(days=dias)).isoformat()

    def _avg(dataset_id: str) -> float | None:
        url = f"{SOCRATA_BASE}/{dataset_id}.json"
        params = {
            "$select": "avg(valorobservado) AS promedio",
            "$where": f"fechaobservacion >= '{fecha_inicio}T00:00:00.000'",
            "$limit": 1,
        }
        try:
            resp = requests.get(url, headers=SOCRATA_HEADERS, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data and data[0].get("promedio") is not None:
                return float(data[0]["promedio"])
        except Exception as e:
            logger.warning(f"[Predict] Error fetching clima {dataset_id}: {e}")
        return None

    prec = _avg(IDEAM_PRECIPITACION_ID) or NORMAL_PRECIPITACION_MM
    temp = _avg(IDEAM_TEMPERATURA_ID) or NORMAL_TEMPERATURA_C

    return {
        "precipitacion_mm": round(prec, 2),
        "temperatura_c": round(temp, 2),
    }


def _interpretar(etiqueta: str, upra: dict, clima: dict) -> str:
    """Genera una interpretación textual del resultado IVT."""
    var = upra.get("variacion_pct", 0)
    prec = clima.get("precipitacion_mm", NORMAL_PRECIPITACION_MM)
    temp = clima.get("temperatura_c", NORMAL_TEMPERATURA_C)

    lineas = []
    if etiqueta == "ALTA":
        lineas.append("⚠️ Vulnerabilidad territorial ALTA.")
        if var > 2:
            lineas.append(f"Los precios de insumos agrícolas subieron {var:.1f}% este mes.")
        if prec < NORMAL_PRECIPITACION_MM * 0.6:
            lineas.append("Se detecta déficit de precipitación (posible sequía).")
        if temp > NORMAL_TEMPERATURA_C + 2:
            lineas.append(f"Temperatura por encima del promedio histórico ({temp:.1f}°C).")
    elif etiqueta == "MEDIA":
        lineas.append("🟡 Vulnerabilidad territorial MEDIA — monitoreo recomendado.")
        if abs(var) > 1:
            dir_ = "subida" if var > 0 else "bajada"
            lineas.append(f"Se observa {dir_} en precios de insumos ({var:+.1f}%).")
    else:
        lineas.append("✅ Vulnerabilidad territorial BAJA — condiciones estables.")

    return " ".join(lineas)
