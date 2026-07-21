"""
backend/app/routers/prediccion.py
==================================
Router /prediccion — Endpoints del modelo de IA territorial (IVT).

Endpoints
---------
GET  /prediccion/actual           — IVT calculado con los datos más recientes
POST /prediccion/simular          — IVT con valores personalizados (simulación)
GET  /prediccion/metadata         — Información del modelo entrenado
POST /prediccion/recargar         — Recarga el modelo desde disco (sin reiniciar)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

router = APIRouter(prefix="/prediccion", tags=["IA — Modelo IVT"])


# ─────────────────────────────────────────────────────────────────────────────
# Modelos de entrada
# ─────────────────────────────────────────────────────────────────────────────

class SimulacionRequest(BaseModel):
    """Parámetros para simular un escenario territorial."""
    upra_indice:        float = Field(..., example=120.5, description="Índice total UPRA")
    upra_var_pct:       float = Field(0.0, example=1.5,  description="Variación mensual % del índice")
    upra_fertilizantes: float = Field(..., example=125.0, description="Subíndice fertilizantes UPRA")
    upra_plaguicidas:   float = Field(..., example=115.0, description="Subíndice plaguicidas UPRA")
    precipitacion_mm:   float = Field(..., example=120.0, description="Precipitación promedio mensual (mm)")
    temperatura_c:      float = Field(..., example=23.5,  description="Temperatura promedio mensual (°C)")
    fecha: Optional[str]     = Field(None, example="2026-06-01", description="Fecha del período (YYYY-MM-DD)")

    class Config:
        json_schema_extra = {
            "example": {
                "upra_indice": 128.5,
                "upra_var_pct": 2.3,
                "upra_fertilizantes": 135.0,
                "upra_plaguicidas": 118.0,
                "precipitacion_mm": 85.0,
                "temperatura_c": 25.0,
            }
        }


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/actual", summary="IVT actual — datos en tiempo real")
async def get_ivt_actual():
    """
    Calcula el Índice de Vulnerabilidad Territorial (IVT) usando los datos
    más recientes disponibles en la API de datos.gov.co.

    - Trae el último mes de UPRA
    - Promedia los últimos 30 días de IDEAM
    - Aplica el modelo Random Forest entrenado

    Si el modelo no está entrenado, retorna instrucciones para hacerlo.
    """
    try:
        from ml.predict import get_ivt_actual
        return get_ivt_actual()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al calcular IVT: {str(e)}")


@router.post("/simular", summary="Simular un escenario territorial")
async def simular_ivt(req: SimulacionRequest):
    """
    Predice el IVT para un conjunto de valores personalizados.

    Permite al usuario explorar escenarios: ¿qué pasa con el IVT si
    la lluvia baja a 50mm/mes y los precios suben 5%?

    Ideal para el asistente interactivo y el panel de análisis del dashboard.
    """
    try:
        from ml.predict import predecir_desde_inputs
        from datetime import date as date_type

        fecha = date_type.fromisoformat(req.fecha) if req.fecha else date_type.today()

        return predecir_desde_inputs(
            upra_indice=req.upra_indice,
            upra_var_pct=req.upra_var_pct,
            upra_fertilizantes=req.upra_fertilizantes,
            upra_plaguicidas=req.upra_plaguicidas,
            precipitacion_mm=req.precipitacion_mm,
            temperatura_c=req.temperatura_c,
            fecha=fecha,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en simulación: {str(e)}")


@router.get("/metadata", summary="Metadata del modelo entrenado")
async def get_modelo_metadata():
    """
    Retorna información sobre el modelo Random Forest entrenado:
    métricas de evaluación, importancia de features, fecha de entrenamiento.

    Si el modelo no está entrenado, indica cómo entrenarlo.
    """
    from ml.modelo_territorial import MODEL_PATH, METADATA_PATH
    import json
    import joblib

    if not MODEL_PATH.exists():
        return {
            "modelo_entrenado": False,
            "instrucciones": "Ejecuta: python -m ml.train",
            "descripcion": (
                "El modelo IVT clasifica períodos en BAJA/MEDIA/ALTA vulnerabilidad "
                "territorial cruzando datos de UPRA, IDEAM y ANI."
            ),
        }

    # Intentar leer metadata desde JSON; si no existe, cargar desde pkl
    metadata = {}
    if METADATA_PATH.exists():
        with open(METADATA_PATH, encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        try:
            data = joblib.load(MODEL_PATH)
            metadata = data.get("metadata", {})
        except Exception:
            metadata = {}

    return {
        "modelo_entrenado": True,
        "ruta": str(MODEL_PATH),
        "algoritmo": "Random Forest Classifier (sklearn)",
        "features": metadata.get("feature_importances", {}),
        "metricas": {
            "cv_f1_macro": metadata.get("cv_f1_mean"),
            "cv_f1_std":   metadata.get("cv_f1_std"),
            "accuracy":    metadata.get("accuracy"),
            "n_train":     metadata.get("n_train"),
        },
        "clases": metadata.get("labels", {0: "BAJA", 1: "MEDIA", 2: "ALTA"}),
        "umbrales_ivt": metadata.get("thresholds", {}),
    }


@router.post("/recargar", summary="Recargar modelo desde disco")
async def recargar_modelo():
    """
    Recarga el modelo desde el archivo pkl sin reiniciar la aplicación.

    Útil para actualizar el modelo después de un reentrenamiento en caliente.
    """
    try:
        from ml.predict import reload_modelo
        ok = reload_modelo()
        if ok:
            return {"status": "ok", "mensaje": "Modelo recargado exitosamente."}
        else:
            return {
                "status": "error",
                "mensaje": "Modelo no encontrado. Ejecuta: python -m ml.train",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
