"""
backend/app/routers/ml_avanzado.py
====================================
Router /ml — Endpoints de ML Avanzado para Kwesx AI.

Endpoints
---------
GET  /ml/estado            — Estado de todos los modelos avanzados
GET  /ml/clustering        — Perfiles territoriales (KMeans + DBSCAN)
GET  /ml/forecast/{serie}  — Predicción de serie temporal (Holt-Winters + SARIMA)
GET  /ml/forecast/series   — Lista de series disponibles para forecast
GET  /ml/anomalias         — Anomalías detectadas en el histórico
POST /ml/anomalias/evaluar — Evaluar si un punto puntual es anómalo
GET  /ml/explicacion       — Explicación XAI de la última predicción IVT
POST /ml/explicacion       — Explicación XAI de predicción específica
GET  /ml/insights          — Resumen ejecutivo de todos los modelos
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/ml", tags=["IA Avanzada — ML, Clustering, Forecasting, XAI"])

MODEL_DIR = Path(__file__).parent.parent.parent.parent / "ml" / "models"


# ─────────────────────────────────────────────────────────────────────────────
# Schemas de entrada
# ─────────────────────────────────────────────────────────────────────────────

class PuntoEvaluacion(BaseModel):
    """Punto de datos para evaluar si es una anomalía."""
    upra_indice_total:            float = Field(115.0, description="Índice UPRA")
    upra_var_mensual_pct:         float = Field(0.0,   description="Variación mensual %")
    upra_fertilizantes:           float = Field(120.0, description="Sub-índice fertilizantes")
    upra_plaguicidas:             float = Field(110.0, description="Sub-índice plaguicidas")
    ideam_precipitacion_mm:       float = Field(150.0, description="Precipitación mm/mes")
    ideam_precipitacion_anomalia: float = Field(0.0,   description="Anomalía vs normal (mm)")
    ideam_temperatura_c:          float = Field(22.0,  description="Temperatura °C")
    ideam_temperatura_anomalia:   float = Field(0.0,   description="Anomalía vs normal (°C)")
    mes:                          int   = Field(6,     description="Mes 1-12")
    anio:                         int   = Field(2026,  description="Año")


class ExplicacionRequest(BaseModel):
    """Parámetros para solicitar una explicación XAI."""
    upra_indice_total:            float = Field(115.0)
    upra_var_mensual_pct:         float = Field(0.0)
    upra_fertilizantes:           float = Field(120.0)
    upra_plaguicidas:             float = Field(110.0)
    ideam_precipitacion_mm:       float = Field(150.0)
    ideam_precipitacion_anomalia: float = Field(0.0)
    ideam_temperatura_c:          float = Field(22.0)
    ideam_temperatura_anomalia:   float = Field(0.0)
    mes:                          int   = Field(6)
    anio:                         int   = Field(2026)


# ─────────────────────────────────────────────────────────────────────────────
# Loaders con singleton pattern (no recargar en cada request)
# ─────────────────────────────────────────────────────────────────────────────

_ensemble_instance = None
_clustering_instance = None
_forecasting_instance = None
_anomaly_instance = None
_xai_instance = None


def _get_ensemble():
    global _ensemble_instance
    if _ensemble_instance is None:
        try:
            from ml.ensemble import EnsembleIVT
            m = EnsembleIVT()
            if m.is_trained():
                m.load()
                _ensemble_instance = m
        except Exception as e:
            logger.warning(f"[ML Router] Ensemble no cargado: {e}")
    return _ensemble_instance


def _get_clustering():
    global _clustering_instance
    if _clustering_instance is None:
        try:
            from ml.clustering import ClusterizadorTerritorial
            m = ClusterizadorTerritorial()
            if m.is_trained():
                m.load()
                _clustering_instance = m
        except Exception as e:
            logger.warning(f"[ML Router] Clustering no cargado: {e}")
    return _clustering_instance


def _get_forecasting():
    global _forecasting_instance
    if _forecasting_instance is None:
        try:
            from ml.forecasting import ForecastingTerritorial
            m = ForecastingTerritorial()
            if m.is_trained():
                m.load()
                _forecasting_instance = m
        except Exception as e:
            logger.warning(f"[ML Router] Forecasting no cargado: {e}")
    return _forecasting_instance


def _get_anomaly():
    global _anomaly_instance
    if _anomaly_instance is None:
        try:
            from ml.anomaly import DetectorAnomalias
            m = DetectorAnomalias()
            if m.is_trained():
                m.load()
                _anomaly_instance = m
        except Exception as e:
            logger.warning(f"[ML Router] Anomaly no cargado: {e}")
    return _anomaly_instance


def _get_xai():
    global _xai_instance
    xai_path = MODEL_DIR / "xai_explainer.pkl"
    if _xai_instance is None and xai_path.exists():
        try:
            import joblib
            _xai_instance = joblib.load(xai_path)
        except Exception as e:
            logger.warning(f"[ML Router] XAI no cargado: {e}")
    return _xai_instance


# ─────────────────────────────────────────────────────────────────────────────
# Helper: respuesta de modelo no disponible
# ─────────────────────────────────────────────────────────────────────────────

def _no_disponible(modelo: str) -> dict[str, Any]:
    return {
        "modelo_disponible": False,
        "modelo": modelo,
        "instrucciones": "Ejecuta: python -m ml.train_advanced",
        "descripcion": f"El modelo '{modelo}' necesita ser entrenado primero.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/estado", summary="Estado de todos los modelos ML avanzados")
async def get_estado_modelos() -> dict[str, Any]:
    """
    Retorna el estado de disponibilidad de todos los modelos avanzados.
    Útil para el dashboard y para verificar qué modelos están listos.
    """
    from ml.ensemble import ENSEMBLE_PATH
    from ml.clustering import CLUSTER_PATH
    from ml.forecasting import FORECAST_PATH
    from ml.anomaly import ANOMALY_PATH

    xai_path = MODEL_DIR / "xai_explainer.pkl"

    estado = {
        "ensemble_ivt": {
            "disponible": ENSEMBLE_PATH.exists(),
            "ruta": str(ENSEMBLE_PATH) if ENSEMBLE_PATH.exists() else None,
        },
        "clustering": {
            "disponible": CLUSTER_PATH.exists(),
            "ruta": str(CLUSTER_PATH) if CLUSTER_PATH.exists() else None,
        },
        "forecasting": {
            "disponible": FORECAST_PATH.exists(),
            "ruta": str(FORECAST_PATH) if FORECAST_PATH.exists() else None,
        },
        "anomaly_detector": {
            "disponible": ANOMALY_PATH.exists(),
            "ruta": str(ANOMALY_PATH) if ANOMALY_PATH.exists() else None,
        },
        "xai_explainer": {
            "disponible": xai_path.exists(),
            "ruta": str(xai_path) if xai_path.exists() else None,
        },
        "instrucciones_entrenamiento": "python -m ml.train_advanced",
    }

    n_disponibles = sum(1 for v in estado.values() if isinstance(v, dict) and v.get("disponible"))
    total = len(estado) - 1
    estado["resumen"] = f"{n_disponibles}/{total} modelos disponibles"

    return estado


@router.get("/clustering", summary="Perfiles territoriales (KMeans + DBSCAN)")
async def get_clustering() -> dict[str, Any]:
    """
    Retorna los perfiles territoriales generados por clustering no supervisado.

    Cada perfil agrupa períodos/zonas con características similares:
    - Perfil de alto riesgo (precios altos + sequía)
    - Perfil de riesgo moderado
    - Perfil favorable
    - Etc. (número de perfiles determinado automáticamente por silhouette score)
    """
    modelo = _get_clustering()
    if modelo is None:
        return _no_disponible("Clustering territorial (KMeans + DBSCAN)")

    return {
        "modelo_disponible": True,
        "algoritmos":        "KMeans (K óptimo por silhouette) + DBSCAN",
        "metadata":          modelo.metadata,
        "perfiles":          {str(k): v for k, v in modelo.perfiles.items()},
        "n_perfiles":        len(modelo.perfiles),
    }


@router.get("/forecast/series", summary="Lista de series disponibles para forecasting")
async def get_series_disponibles() -> dict[str, Any]:
    """Lista las series temporales que tienen modelos de forecast entrenados."""
    modelo = _get_forecasting()
    if modelo is None:
        return {**_no_disponible("Forecasting"), "series": []}

    return {
        "modelo_disponible": True,
        "series": modelo.series_disponibles(),
    }


@router.get("/forecast/{serie}", summary="Predicción de serie temporal")
async def get_forecast(
    serie: str,
    horizonte: int = Query(default=6, ge=1, le=24, description="Meses a pronosticar (1-24)"),
) -> dict[str, Any]:
    """
    Genera el pronóstico para una serie temporal específica.

    Series disponibles:
    - `upra_indice_total` — Índice de precios de insumos agrícolas
    - `ideam_precipitacion_mm` — Precipitación mensual
    - `ideam_temperatura_c` — Temperatura mensual

    Retorna predicciones mensuales con intervalos de confianza al 95%.
    """
    modelo = _get_forecasting()
    if modelo is None:
        return _no_disponible("Forecasting (Holt-Winters + SARIMA)")

    try:
        resultado = modelo.forecast(serie, horizonte=horizonte)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en forecast: {str(e)}")

    if "error" in resultado:
        raise HTTPException(status_code=404, detail=resultado["error"])

    return {"modelo_disponible": True, **resultado}


@router.get("/anomalias", summary="Anomalías detectadas en el histórico")
async def get_anomalias(top: int = Query(default=10, ge=1, le=50)) -> dict[str, Any]:
    """
    Detecta anomalías en el histórico completo de datos territoriales.

    Usa Isolation Forest + LOF para identificar períodos con
    comportamiento atípico multivariado (precios + clima combinados).

    Retorna las anomalías ordenadas por severidad (más críticas primero).
    """
    modelo = _get_anomaly()
    if modelo is None:
        return _no_disponible("Detector de Anomalías (Isolation Forest + LOF)")

    try:
        from ml.features import build_feature_matrix_from_api
        df = build_feature_matrix_from_api()
        resultado = modelo.detectar(df)

        # Limitar a top N
        resultado["anomalias"] = resultado["anomalias"][:top]
        return {"modelo_disponible": True, **resultado}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en detección: {str(e)}")


@router.post("/anomalias/evaluar", summary="Evaluar si un punto es una anomalía")
async def evaluar_anomalia(punto: PuntoEvaluacion) -> dict[str, Any]:
    """
    Evalúa si un conjunto de valores específico corresponde a un período anómalo.

    Útil para el asistente y el simulador de escenarios:
    permite al usuario preguntar "¿Estos valores son normales?"
    """
    modelo = _get_anomaly()
    if modelo is None:
        return _no_disponible("Detector de Anomalías")

    try:
        resultado = modelo.predict_fila(punto.model_dump())
        return {"modelo_disponible": True, **resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explicacion", summary="Explicación XAI de la predicción IVT actual")
async def get_explicacion_actual() -> dict[str, Any]:
    """
    Genera la explicación SHAP de la predicción IVT más reciente.

    Retorna:
    - Factores más importantes (globales y para esta predicción)
    - Explicación en lenguaje natural para ciudadanos
    - Explicación técnica con valores SHAP
    - Datos para gráfica de contribuciones
    """
    xai = _get_xai()
    ensemble = _get_ensemble()

    if xai is None:
        return _no_disponible("XAI Explainer (SHAP)")
    if ensemble is None:
        return _no_disponible("Ensemble IVT")

    try:
        import pandas as pd
        from ml.predict import _fetch_ultimo_upra, _fetch_clima_reciente
        from ml.features import build_prediction_features, NORMAL_PRECIPITACION_MM, NORMAL_TEMPERATURA_C
        from datetime import date

        upra  = _fetch_ultimo_upra()
        clima = _fetch_clima_reciente(dias=30)

        X = build_prediction_features(
            upra_indice=upra.get("indice_total", 115.0),
            upra_var_pct=upra.get("variacion_pct", 0.0),
            upra_fertilizantes=upra.get("total_fertilizantes", 120.0),
            upra_plaguicidas=upra.get("total_plaguicidas", 110.0),
            precipitacion_mm=clima.get("precipitacion_mm", NORMAL_PRECIPITACION_MM),
            temperatura_c=clima.get("temperatura_c", NORMAL_TEMPERATURA_C),
            fecha=date.today(),
        )

        pred   = ensemble.predict(X)
        explic = xai.explicar(X, etiqueta=pred["etiqueta"], pipeline=ensemble.pipeline)

        return {"modelo_disponible": True, "prediccion": pred, **explic}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en XAI: {str(e)}")


@router.post("/explicacion", summary="Explicación XAI para valores específicos")
async def post_explicacion(req: ExplicacionRequest) -> dict[str, Any]:
    """
    Genera la explicación SHAP para un conjunto de valores dado por el usuario.
    Ideal para el simulador de escenarios: "¿Por qué este escenario es ALTA?"
    """
    xai = _get_xai()
    ensemble = _get_ensemble()

    if xai is None:
        return _no_disponible("XAI Explainer")
    if ensemble is None:
        return _no_disponible("Ensemble IVT")

    try:
        import pandas as pd
        from ml.features import FEATURE_COLS

        X = pd.DataFrame([req.model_dump()])[FEATURE_COLS]
        pred   = ensemble.predict(X)
        explic = xai.explicar(X, etiqueta=pred["etiqueta"], pipeline=ensemble.pipeline)

        return {"modelo_disponible": True, "prediccion": pred, **explic}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights", summary="Resumen ejecutivo IA de todos los modelos")
async def get_insights_ia() -> dict[str, Any]:
    """
    Genera un resumen ejecutivo automático combinando todos los modelos.

    Incluye:
    - IVT actual (ensemble)
    - Tendencia de precios (forecasting)
    - Perfil territorial del período actual (clustering)
    - Anomalías recientes detectadas
    - Recomendaciones automáticas

    Este endpoint alimenta el panel de Insights del dashboard principal.
    """
    insights: dict[str, Any] = {
        "generado_en": __import__("datetime").datetime.now().isoformat(),
        "fuente":      "Kwesx AI — Ensemble RF+XGBoost, Clustering KMeans+DBSCAN, SARIMA, IsoForest",
    }

    # IVT actual
    try:
        from ml.predict import get_ivt_actual
        ivt = get_ivt_actual()
        insights["ivt_actual"] = ivt
    except Exception as e:
        insights["ivt_actual"] = {"error": str(e)}

    # Forecasting UPRA (3 meses)
    forecasting = _get_forecasting()
    if forecasting:
        try:
            fc = forecasting.forecast("upra_indice_total", horizonte=3)
            insights["forecast_precios"] = {
                "cambio_esperado_3m_pct": fc.get("cambio_esperado_pct"),
                "interpretacion":         fc.get("interpretacion"),
                "predicciones":           fc.get("predicciones", []),
            }
        except Exception as e:
            insights["forecast_precios"] = {"error": str(e)}
    else:
        insights["forecast_precios"] = {"modelo_disponible": False}

    # Clustering — perfil del período actual
    clustering = _get_clustering()
    if clustering:
        insights["perfiles_territoriales"] = {
            "n_perfiles": len(clustering.perfiles),
            "perfiles":   {str(k): v["nombre"] for k, v in clustering.perfiles.items()},
            "metadata":   clustering.metadata.get("kmeans", {}),
        }
    else:
        insights["perfiles_territoriales"] = {"modelo_disponible": False}

    # Anomalías recientes
    anomaly = _get_anomaly()
    if anomaly:
        try:
            from ml.features import build_feature_matrix_from_api
            df = build_feature_matrix_from_api()
            res = anomaly.detectar(df)
            insights["anomalias"] = {
                "n_anomalias":          res["n_anomalias"],
                "tasa_pct":             res["tasa_anomalia_pct"],
                "mas_recientes":        res["anomalias"][:3],
                "interpretacion":       res["interpretacion"],
            }
        except Exception as e:
            insights["anomalias"] = {"error": str(e)}
    else:
        insights["anomalias"] = {"modelo_disponible": False}

    # XAI — importancias globales
    xai = _get_xai()
    if xai:
        insights["xai"] = {
            "importancias_globales": xai.get_importancias_api()[:5],
            "shap_disponible":       True,
        }
    else:
        insights["xai"] = {"modelo_disponible": False}

    # Recomendaciones automáticas
    insights["recomendaciones"] = _generar_recomendaciones(insights)

    return insights


def _generar_recomendaciones(insights: dict[str, Any]) -> list[dict[str, str]]:
    """Genera recomendaciones automáticas basadas en todos los modelos."""
    recomendaciones: list[dict[str, str]] = []

    # Basada en IVT
    ivt = insights.get("ivt_actual", {}).get("ivt", {})
    etiqueta = ivt.get("etiqueta", "")
    if etiqueta == "ALTA":
        recomendaciones.append({
            "tipo":     "ALERTA",
            "icono":    "⚠️",
            "titulo":   "Vulnerabilidad territorial alta",
            "accion":   "Activar protocolo de asistencia a agricultores en zonas afectadas.",
            "prioridad":"ALTA",
        })
    elif etiqueta == "MEDIA":
        recomendaciones.append({
            "tipo":     "MONITOREO",
            "icono":    "🔍",
            "titulo":   "Monitoreo reforzado recomendado",
            "accion":   "Aumentar frecuencia de seguimiento a precios y condiciones climáticas.",
            "prioridad":"MEDIA",
        })

    # Basada en forecast
    cambio_fc = insights.get("forecast_precios", {}).get("cambio_esperado_3m_pct")
    if cambio_fc and cambio_fc > 5:
        recomendaciones.append({
            "tipo":     "PREVENCIÓN",
            "icono":    "📈",
            "titulo":   f"Precios al alza: +{cambio_fc:.1f}% en 3 meses",
            "accion":   "Considerar compra anticipada de insumos antes del pico proyectado.",
            "prioridad":"MEDIA",
        })

    # Basada en anomalías
    n_anom = insights.get("anomalias", {}).get("n_anomalias", 0)
    if n_anom > 5:
        recomendaciones.append({
            "tipo":     "INVESTIGACIÓN",
            "icono":    "🔬",
            "titulo":   f"{n_anom} períodos anómalos detectados",
            "accion":   "Revisar datos históricos anómalos para identificar causas estructurales.",
            "prioridad":"BAJA",
        })

    # Recomendación general si no hay alertas
    if not recomendaciones:
        recomendaciones.append({
            "tipo":     "INFO",
            "icono":    "✅",
            "titulo":   "Condiciones territoriales estables",
            "accion":   "Continuar con el monitoreo regular de indicadores clave.",
            "prioridad":"BAJA",
        })

    return recomendaciones


# -- Endpoint de validacion --------------------------------------------------

@router.get("/validacion", summary="Metricas de validacion del modelo IVT")
async def get_validacion() -> dict[str, Any]:
    """
    Retorna las metricas de validacion del modelo IVT Ensemble.

    Incluye accuracy, F1-score, AUC-ROC, matriz de confusion,
    validacion cruzada e importancia de variables.

    Las metricas se calculan sobre datos de prueba al primer acceso
    y se cachean en ml/models/validation.json para accesos subsiguientes.
    """
    import json as _json
    val_path = MODEL_DIR / "validation.json"

    # Intentar cargar desde cache
    if val_path.exists():
        try:
            with open(val_path, encoding="utf-8") as f:
                cached = _json.load(f)
            return {
                "modelo_disponible": True,
                "desde_cache":       True,
                "metricas":          cached,
            }
        except Exception:
            pass

    # Calcular metricas en tiempo real
    try:
        import sys
        ROOT = MODEL_DIR.parent.parent.parent
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))

        from ml.validation_report import (
            cargar_modelo, generar_datos_prueba,
            calcular_metricas, calcular_cv, calcular_importancias,
        )

        modelo, _ = cargar_modelo()
        X, y = generar_datos_prueba(n=500)

        # Entrenar si no esta listo
        try:
            modelo.predict(X.head(1))
        except Exception:
            X_train, y_train = generar_datos_prueba(n=2000, seed=0)
            modelo.fit(X_train, y_train)

        metricas     = calcular_metricas(modelo, X, y)
        cv           = calcular_cv(modelo, X, y)
        importancias = calcular_importancias(modelo)

        resultado = {**metricas, "cv": cv, "importancias": importancias}

        # Guardar cache
        val_path.parent.mkdir(parents=True, exist_ok=True)
        with open(val_path, "w", encoding="utf-8") as f:
            _json.dump(resultado, f, indent=2, ensure_ascii=False)

        return {
            "modelo_disponible": True,
            "desde_cache":       False,
            "metricas":          resultado,
        }

    except Exception as e:
        logger.warning(f"No se pudo calcular validacion: {e}")
        return {
            "modelo_disponible": False,
            "mensaje": (
                "El modelo IVT no esta entrenado aun. "
                "Ejecuta 'python -m ml.train_advanced' para entrenar el modelo."
            ),
            "error": str(e),
        }
