"""
ml/anomaly.py
=============
Detección de anomalías territoriales para Kwesx AI.

Algoritmos
----------
1. Isolation Forest — Aísla outliers multivariados de forma eficiente.
   Detecta períodos con comportamiento atípico en combinación de features.

2. LOF (Local Outlier Factor) — Detecta anomalías basadas en densidad local.
   Útil para series con grupos de distinta densidad.

3. Z-Score univariado — Detección rápida de outliers en series individuales.
   Complementa los modelos multivariados con señales claras por variable.

Tipos de anomalías detectadas
------------------------------
- Pico de precios inusual (UPRA sube > 3σ en un mes)
- Sequía extrema (precipitación < percentil 5 histórico)
- Ola de calor (temperatura > percentil 95)
- Combinación de múltiples señales simultáneas (riesgo compuesto)

Output del análisis
-------------------
{
  "n_anomalias":  8,
  "tasa_anomalia": 9.0,
  "anomalias": [
    {
      "periodo":    "2023-04",
      "tipo":       "precio_extremo",
      "severidad":  "ALTA",
      "descripcion":"Los precios de insumos subieron 4.2σ sobre el promedio histórico",
      "variables":  {"upra_indice_total": 142.3, "upra_var_mensual_pct": 6.8},
      "score":      -0.89
    }
  ],
  "serie_anomalia_score": [...],
  "interpretacion": "..."
}
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

from ml.features import FEATURE_COLS

# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

MODEL_DIR      = Path(__file__).parent / "models"
ANOMALY_PATH   = MODEL_DIR / "anomaly_detector.pkl"
ANOMALY_META   = MODEL_DIR / "anomaly_metadata.json"

# Features más relevantes para detección de anomalías (excluir temporales)
ANOMALY_FEATURES = [
    "upra_indice_total",
    "upra_var_mensual_pct",
    "upra_fertilizantes",
    "upra_plaguicidas",
    "ideam_precipitacion_mm",
    "ideam_precipitacion_anomalia",
    "ideam_temperatura_c",
    "ideam_temperatura_anomalia",
]

# Umbrales Z-score para clasificar severidad
Z_MODERADO = 2.0
Z_ALTO     = 2.5
Z_CRITICO  = 3.0


# ─────────────────────────────────────────────────────────────────────────────
# Clase principal
# ─────────────────────────────────────────────────────────────────────────────

class DetectorAnomalias:
    """
    Sistema de detección de anomalías territoriales multivariado.

    Combina Isolation Forest (outliers multivariados) + LOF (densidad local)
    + Z-Score univariado para una cobertura completa de tipos de anomalía.
    """

    def __init__(self, contamination: float = 0.10):
        """
        contamination : Fracción esperada de outliers en los datos (0.0-0.5).
                        Default 0.10 = se espera que ~10% de los períodos sean anómalos.
        """
        self.contamination = contamination
        self.iso_forest: IsolationForest | None = None
        self.lof: LocalOutlierFactor | None = None
        self.scaler: StandardScaler | None = None
        self.estadisticas: dict[str, Any] = {}   # Media y std por feature
        self.metadata: dict[str, Any] = {}

    # ── Entrenamiento ─────────────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Entrena los detectores de anomalías.

        Parámetros
        ----------
        df : DataFrame con columnas de ANOMALY_FEATURES disponibles.

        Retorna metadatos del entrenamiento.
        """
        cols = [c for c in ANOMALY_FEATURES if c in df.columns]
        if not cols:
            raise ValueError("No hay features de anomalías disponibles en el DataFrame.")
        if len(df) < 10:
            raise ValueError(f"Se necesitan al menos 10 filas: {len(df)} recibidas.")

        X = df[cols].fillna(0.0)

        # Normalizar
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Estadísticas por feature (para Z-score univariado)
        self.estadisticas = {
            col: {
                "media": float(X[col].mean()),
                "std":   max(float(X[col].std()), 1e-6),
                "p05":   float(X[col].quantile(0.05)),
                "p95":   float(X[col].quantile(0.95)),
            }
            for col in cols
        }

        # Isolation Forest
        n_estimators = min(200, max(50, len(df) * 2))
        self.iso_forest = IsolationForest(
            n_estimators=n_estimators,
            contamination=self.contamination,
            max_samples=min(len(df), 256),
            random_state=2026,
            n_jobs=-1,
        )
        self.iso_forest.fit(X_scaled)

        # LOF (solo para predicción, sin fit necesario al no ser novelty)
        self.lof = LocalOutlierFactor(
            n_neighbors=min(20, len(df) // 3 + 1),
            contamination=self.contamination,
            novelty=True,   # novelty=True permite .predict() en nuevos datos
        )
        self.lof.fit(X_scaled)

        self.metadata = {
            "features_usadas":  cols,
            "n_muestras":       len(df),
            "contamination":    self.contamination,
            "n_estimators_if":  n_estimators,
            "entrenado_en":     datetime.now().isoformat(),
        }

        logger.success(
            f"[Anomaly] Detectores entrenados: IF({n_estimators}) + LOF "
            f"sobre {len(df)} muestras con {len(cols)} features."
        )
        return self.metadata

    # ── Detección ─────────────────────────────────────────────────────────────

    def detectar(
        self,
        df: pd.DataFrame,
        fecha_col: str = "fecha",
        periodo_col: str = "anio_mes",
    ) -> dict[str, Any]:
        """
        Detecta anomalías en el DataFrame completo.

        Retorna un dict con la lista de anomalías, scores y estadísticas.
        """
        if self.iso_forest is None or self.scaler is None:
            raise RuntimeError("Detector no entrenado. Ejecuta fit() primero.")

        cols = [c for c in ANOMALY_FEATURES if c in df.columns]
        X = df[cols].fillna(0.0)
        X_scaled = self.scaler.transform(X)

        # Scores de Isolation Forest (más negativo = más anómalo)
        if_scores   = self.iso_forest.score_samples(X_scaled)   # rango ~(-1, 0)
        if_etiqueta = self.iso_forest.predict(X_scaled)         # -1=outlier, 1=normal

        # Scores de LOF (más negativo = más anómalo)
        try:
            lof_scores   = -self.lof.score_samples(X_scaled)   # positivo = anómalo
            lof_etiqueta = self.lof.predict(X_scaled)           # -1=outlier, 1=normal
        except Exception:
            lof_scores   = np.zeros(len(df))
            lof_etiqueta = np.ones(len(df))

        # Ensemble: es anomalía si IF o LOF lo marcan como tal
        es_anomalia = (if_etiqueta == -1) | (lof_etiqueta == -1)

        # Score combinado (0 = normal, 1 = muy anómalo)
        if_norm  = (-if_scores - (-if_scores).min()) / ((-if_scores).max() - (-if_scores).min() + 1e-9)
        lof_norm = (lof_scores - lof_scores.min()) / (lof_scores.max() - lof_scores.min() + 1e-9)
        score_combinado = 0.6 * if_norm + 0.4 * lof_norm

        # Análisis Z-score univariado
        z_scores = self._calcular_z_scores(df[cols])

        # Construir lista de anomalías
        anomalias = []
        for i in range(len(df)):
            if not es_anomalia[i]:
                continue

            fila = df.iloc[i]
            periodo = self._get_periodo(fila, fecha_col, periodo_col)
            tipo, severidad, descripcion = self._clasificar_anomalia(
                fila, cols, z_scores.iloc[i]
            )

            anomalias.append({
                "periodo":      periodo,
                "tipo":         tipo,
                "severidad":    severidad,
                "descripcion":  descripcion,
                "score_if":     round(float(if_scores[i]), 4),
                "score_combinado": round(float(score_combinado[i]), 4),
                "variables":    {
                    c: round(float(fila[c]), 3) for c in cols if c in fila.index
                },
                "z_scores":     {
                    c: round(float(z_scores.iloc[i][c]), 3) for c in cols if c in z_scores.columns
                },
            })

        # Ordenar por score (las más anómalas primero)
        anomalias.sort(key=lambda a: a["score_combinado"], reverse=True)

        # Serie temporal de scores
        serie_scores = [
            {
                "periodo": self._get_periodo(df.iloc[i], fecha_col, periodo_col),
                "score":   round(float(score_combinado[i]), 4),
                "es_anomalia": bool(es_anomalia[i]),
            }
            for i in range(len(df))
        ]

        tasa = round(100 * es_anomalia.sum() / len(df), 2)
        return {
            "n_total":          len(df),
            "n_anomalias":      int(es_anomalia.sum()),
            "tasa_anomalia_pct":tasa,
            "anomalias":        anomalias,
            "serie_scores":     serie_scores,
            "interpretacion":   self._interpretar(anomalias, tasa),
        }

    def _calcular_z_scores(self, X: pd.DataFrame) -> pd.DataFrame:
        """Calcula Z-scores univariados para cada feature."""
        z = pd.DataFrame(index=X.index)
        for col in X.columns:
            if col in self.estadisticas:
                s = self.estadisticas[col]
                z[col] = (X[col] - s["media"]) / s["std"]
            else:
                z[col] = 0.0
        return z

    def _get_periodo(
        self,
        fila: pd.Series,
        fecha_col: str,
        periodo_col: str,
    ) -> str:
        """Extrae el período como string."""
        for col in [periodo_col, fecha_col]:
            if col in fila.index and pd.notna(fila[col]):
                v = fila[col]
                if hasattr(v, "strftime"):
                    return v.strftime("%Y-%m")
                return str(v)[:7]
        return "desconocido"

    def _clasificar_anomalia(
        self,
        fila: pd.Series,
        cols: list[str],
        z_row: pd.Series,
    ) -> tuple[str, str, str]:
        """Clasifica el tipo y severidad de una anomalía."""
        max_z = z_row.abs().max()
        feature_max = z_row.abs().idxmax() if not z_row.empty else ""

        # Severidad
        if max_z >= Z_CRITICO:
            severidad = "CRÍTICA"
        elif max_z >= Z_ALTO:
            severidad = "ALTA"
        else:
            severidad = "MODERADA"

        # Tipo y descripción
        z_upra = z_row.get("upra_var_mensual_pct", 0)
        z_prec = z_row.get("ideam_precipitacion_anomalia", 0)
        z_temp = z_row.get("ideam_temperatura_anomalia", 0)

        if abs(z_upra) >= Z_MODERADO and abs(z_prec) >= Z_MODERADO:
            tipo = "riesgo_compuesto"
            descripcion = (
                f"Coincidencia de precio atípico ({z_upra:+.1f}σ) "
                f"y anomalía climática ({z_prec:+.1f}σ). "
                f"Riesgo territorial elevado."
            )
        elif z_upra >= Z_MODERADO:
            tipo = "precio_extremo"
            descripcion = (
                f"Aumento atípico en precios de insumos: {z_upra:+.1f}σ sobre el promedio histórico. "
                f"Posible impacto en costos agrícolas."
            )
        elif z_upra <= -Z_MODERADO:
            tipo = "precio_minimo"
            descripcion = (
                f"Caída atípica en precios de insumos: {z_upra:+.1f}σ bajo el promedio. "
                f"Posible deflación o caída de demanda."
            )
        elif z_prec <= -Z_MODERADO:
            tipo = "sequia_extrema"
            descripcion = (
                f"Déficit hídrico severo: precipitación {abs(z_prec):.1f}σ "
                f"bajo la normal histórica. Riesgo de sequía."
            )
        elif z_prec >= Z_MODERADO:
            tipo = "exceso_hidrico"
            descripcion = (
                f"Exceso hídrico: precipitación {z_prec:.1f}σ sobre la normal. "
                f"Riesgo de inundaciones o exceso de humedad."
            )
        elif z_temp >= Z_MODERADO:
            tipo = "ola_calor"
            descripcion = (
                f"Temperatura anormalmente alta: {z_temp:+.1f}σ sobre el promedio. "
                f"Posible estrés térmico en cultivos."
            )
        else:
            tipo = "anomalia_multivariada"
            descripcion = (
                f"Combinación inusual de condiciones detectada "
                f"(feature más extrema: {feature_max}, z={max_z:+.1f}σ)."
            )

        return tipo, severidad, descripcion

    def _interpretar(self, anomalias: list[dict], tasa: float) -> str:
        """Genera una interpretación general del resultado."""
        if not anomalias:
            return "No se detectaron períodos con comportamiento atípico significativo."

        tipos_count: dict[str, int] = {}
        for a in anomalias:
            tipos_count[a["tipo"]] = tipos_count.get(a["tipo"], 0) + 1

        tipo_mas_comun = max(tipos_count, key=lambda k: tipos_count[k])
        criticas = sum(1 for a in anomalias if a["severidad"] == "CRÍTICA")

        partes = [f"Se detectaron {len(anomalias)} períodos anómalos ({tasa}% de la serie)."]
        if criticas:
            partes.append(f"{criticas} anomalías de severidad crítica requieren atención inmediata.")
        partes.append(
            f"El patrón más frecuente es '{tipo_mas_comun.replace('_', ' ')}' "
            f"({tipos_count[tipo_mas_comun]} ocurrencias)."
        )
        return " ".join(partes)

    # ── Predicción puntual ────────────────────────────────────────────────────

    def predict_fila(self, fila: dict[str, float]) -> dict[str, Any]:
        """Evalúa si una observación puntual es una anomalía."""
        if self.iso_forest is None:
            raise RuntimeError("Detector no entrenado.")

        cols = [c for c in ANOMALY_FEATURES if c in fila]
        X = np.array([[fila.get(c, 0.0) for c in ANOMALY_FEATURES]])
        X_scaled = self.scaler.transform(X)

        score  = float(self.iso_forest.score_samples(X_scaled)[0])
        etiq   = int(self.iso_forest.predict(X_scaled)[0])  # -1 o 1

        return {
            "es_anomalia":  etiq == -1,
            "score":        round(score, 4),
            "interpretacion": "Período anómalo detectado." if etiq == -1 else "Período con comportamiento normal.",
        }

    # ── Persistencia ──────────────────────────────────────────────────────────

    def save(self) -> str:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "iso_forest":    self.iso_forest,
            "lof":           self.lof,
            "scaler":        self.scaler,
            "estadisticas":  self.estadisticas,
            "metadata":      self.metadata,
        }, ANOMALY_PATH)
        with open(ANOMALY_META, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        logger.success(f"[Anomaly] Guardado en {ANOMALY_PATH}")
        return str(ANOMALY_PATH)

    def load(self) -> "DetectorAnomalias":
        if not ANOMALY_PATH.exists():
            raise FileNotFoundError(f"Detector no encontrado en {ANOMALY_PATH}.")
        data = joblib.load(ANOMALY_PATH)
        self.iso_forest    = data["iso_forest"]
        self.lof           = data["lof"]
        self.scaler        = data["scaler"]
        self.estadisticas  = data.get("estadisticas", {})
        self.metadata      = data.get("metadata", {})
        logger.info(f"[Anomaly] Cargado desde {ANOMALY_PATH}")
        return self

    def is_trained(self) -> bool:
        return ANOMALY_PATH.exists()
