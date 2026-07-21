"""
ml/explainability.py
====================
Explainable AI (XAI) para Kwesx AI — basado en SHAP.

¿Por qué SHAP?
--------------
SHAP (SHapley Additive exPlanations) es el estándar de facto para XAI en
modelos de árboles. Tiene garantías matemáticas de consistencia y exactitud
que LIME no tiene. Para RF y XGBoost usa TreeExplainer, que es O(TLD²)
— muy rápido incluso en datasets grandes.

Outputs generados
-----------------
1. Importancias globales SHAP (promedio |SHAP| por feature)
2. Valores SHAP de una predicción puntual (waterfall plot data)
3. Explicación en lenguaje natural para ciudadanos
4. Explicación técnica para investigadores
5. Gráfico de barras de contribuciones (datos para frontend)

Ejemplos de output
------------------
Para una predicción ALTA:
  "Los precios de fertilizantes subieron 6.8% este mes (+4.2 puntos al riesgo).
   La sequía de las últimas semanas (+3.1 puntos) agravó la situación.
   El período de cosecha (septiembre-noviembre) aumenta históricamente el riesgo (+2.8 puntos)."

Uso
---
    from ml.explainability import ExplicadorIVT
    explicador = ExplicadorIVT()
    explicador.fit(modelo_pipeline, X_train)
    resultado = explicador.explicar(X_fila, etiqueta="ALTA")
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# Importar SHAP (opcional — si no está instalado, las explicaciones son
# degradadas pero la plataforma sigue funcionando)
# ─────────────────────────────────────────────────────────────────────────────

try:
    import shap
    SHAP_DISPONIBLE = True
except ImportError:
    SHAP_DISPONIBLE = False
    logger.warning("[XAI] SHAP no instalado. pip install shap==0.45.1")

from ml.features import FEATURE_COLS

# ─────────────────────────────────────────────────────────────────────────────
# Nombres legibles para las features (para el ciudadano)
# ─────────────────────────────────────────────────────────────────────────────

NOMBRES_FEATURES = {
    "upra_indice_total":             "Nivel de precios de insumos agrícolas",
    "upra_var_mensual_pct":          "Cambio mensual en precio de insumos (%)",
    "upra_fertilizantes":            "Precio de fertilizantes",
    "upra_plaguicidas":              "Precio de plaguicidas y agroquímicos",
    "ideam_precipitacion_mm":        "Lluvia mensual (mm)",
    "ideam_precipitacion_anomalia":  "Déficit o exceso de lluvia vs. normal",
    "ideam_temperatura_c":           "Temperatura media mensual (°C)",
    "ideam_temperatura_anomalia":    "Temperatura fuera de lo normal",
    "mes":                           "Mes del año (estacionalidad)",
    "anio":                          "Año (tendencia histórica)",
}

UMBRAL_SHAP_RELEVANTE = 0.5  # Contribución mínima para mencionar en explicación ciudadana


# ─────────────────────────────────────────────────────────────────────────────
# Clase principal
# ─────────────────────────────────────────────────────────────────────────────

class ExplicadorIVT:
    """
    Motor de Explainable AI para el modelo IVT de Kwesx AI.

    Genera explicaciones en dos niveles:
    - Ciudadano: lenguaje natural, sin jerga técnica
    - Investigador: valores SHAP numéricos, importancias, gráficas
    """

    def __init__(self):
        self.explainer: Any = None
        self.shap_values_global: np.ndarray | None = None
        self.X_train: pd.DataFrame | None = None
        self.importancias_globales: dict[str, float] = {}
        self.clases_modelo: list[str] = []

    # ── Ajuste ────────────────────────────────────────────────────────────────

    def fit(
        self,
        pipeline: Any,
        X_train: pd.DataFrame,
        class_names: list[str] | None = None,
    ) -> "ExplicadorIVT":
        """
        Inicializa el explainer SHAP con el modelo entrenado.

        Parámetros
        ----------
        pipeline    : sklearn Pipeline (scaler + classifier)
        X_train     : DataFrame de entrenamiento (columnas = FEATURE_COLS)
        class_names : Nombres de las clases (ej: ["BAJA","MEDIA","ALTA"])
        """
        if not SHAP_DISPONIBLE:
            logger.warning("[XAI] SHAP no disponible. Usando importancias por permutación.")
            self._fit_sin_shap(pipeline, X_train)
            return self

        self.X_train = X_train[FEATURE_COLS].fillna(0.0)
        self.clases_modelo = class_names or ["BAJA", "MEDIA", "ALTA"]

        # Extraer el clasificador base del pipeline
        clf = self._extraer_clasificador(pipeline)

        # Escalar los datos de entrenamiento
        scaler = pipeline.named_steps.get("scaler")
        X_scaled = scaler.transform(self.X_train) if scaler is not None else self.X_train.values

        try:
            # TreeExplainer: óptimo para RF, XGBoost, LightGBM
            self.explainer = shap.TreeExplainer(
                clf,
                data=X_scaled,
                feature_perturbation="interventional",
            )

            # Calcular SHAP globales (muestra de hasta 100 filas para eficiencia)
            sample = X_scaled[:min(100, len(X_scaled))]
            self.shap_values_global = self.explainer.shap_values(sample)

            # Importancias globales: |SHAP| promedio por feature
            self._calcular_importancias_globales()

            logger.success(
                f"[XAI] SHAP TreeExplainer listo. "
                f"{len(FEATURE_COLS)} features | "
                f"Clases: {self.clases_modelo}"
            )
        except Exception as e:
            logger.warning(f"[XAI] TreeExplainer falló ({e}). Usando KernelExplainer...")
            self._fit_kernel(clf, X_scaled)

        return self

    def _extraer_clasificador(self, pipeline: Any) -> Any:
        """Extrae el clasificador base de pipelines anidados."""
        clf = pipeline.named_steps.get("classifier")

        # VotingClassifier (Ensemble) → usar el primer estimador (RF calibrado)
        if hasattr(clf, "estimators_") and hasattr(clf, "voting"):
            try:
                calibrado = clf.estimators_[0]
                # CalibratedClassifierCV → base_estimator
                if hasattr(calibrado, "calibrated_classifiers_"):
                    return calibrado.calibrated_classifiers_[0].estimator
            except Exception:
                pass

        # CalibratedClassifierCV directo
        if hasattr(clf, "calibrated_classifiers_"):
            return clf.calibrated_classifiers_[0].estimator

        return clf

    def _fit_sin_shap(self, pipeline: Any, X_train: pd.DataFrame) -> None:
        """Fallback cuando SHAP no está instalado: importancias de permutación."""
        self.X_train = X_train[FEATURE_COLS].fillna(0.0)
        try:
            clf = self._extraer_clasificador(pipeline)
            if hasattr(clf, "feature_importances_"):
                imps = clf.feature_importances_
                self.importancias_globales = {
                    f: round(float(v), 4)
                    for f, v in zip(FEATURE_COLS, imps)
                }
        except Exception:
            self.importancias_globales = {f: 0.0 for f in FEATURE_COLS}

    def _fit_kernel(self, clf: Any, X_scaled: np.ndarray) -> None:
        """Fallback con KernelExplainer (más lento pero universal)."""
        try:
            background = shap.kmeans(X_scaled, min(50, len(X_scaled)))
            self.explainer = shap.KernelExplainer(
                lambda x: clf.predict_proba(x) if hasattr(clf, "predict_proba") else clf.predict(x),
                background,
            )
            sample = X_scaled[:min(30, len(X_scaled))]
            self.shap_values_global = self.explainer.shap_values(sample)
            self._calcular_importancias_globales()
        except Exception as e:
            logger.warning(f"[XAI] KernelExplainer también falló: {e}")

    def _calcular_importancias_globales(self) -> None:
        """Calcula importancias globales promediando |SHAP| sobre todas las clases."""
        if self.shap_values_global is None:
            return

        sv = self.shap_values_global
        if isinstance(sv, list):
            # Multiclase: lista de matrices [n_samples x n_features] por clase
            abs_mean = np.mean([np.abs(c).mean(axis=0) for c in sv], axis=0)
        else:
            abs_mean = np.abs(sv).mean(axis=0)

        self.importancias_globales = {
            FEATURE_COLS[i]: round(float(abs_mean[i]), 4)
            for i in range(min(len(FEATURE_COLS), len(abs_mean)))
        }

    # ── Explicación puntual ───────────────────────────────────────────────────

    def explicar(
        self,
        X: pd.DataFrame,
        etiqueta: str = "?",
        pipeline: Any = None,
    ) -> dict[str, Any]:
        """
        Genera la explicación completa para una predicción puntual.

        Parámetros
        ----------
        X        : DataFrame de 1 fila con las features del período a explicar
        etiqueta : Clase predicha ("BAJA", "MEDIA", "ALTA")
        pipeline : Pipeline del modelo (necesario para escalar X)

        Retorna
        -------
        {
          "nivel":           "ALTA",
          "contribuciones":  {...},  # por feature, espacio SHAP
          "top_factores":    [...],  # 3-5 factores más importantes
          "explicacion_ciudadano":  "...",
          "explicacion_tecnica":    "...",
          "importancias_globales":  {...},
          "grafica_datos":          [...],  # para Recharts/Chart.js
        }
        """
        X_clean = X[FEATURE_COLS].fillna(0.0)

        # Escalar si hay pipeline
        scaler = pipeline.named_steps.get("scaler") if pipeline else None
        X_arr = scaler.transform(X_clean) if scaler is not None else X_clean.values

        # Obtener valores SHAP para esta fila
        contribuciones = self._shap_fila(X_arr, etiqueta)

        # Top factores (ordenados por |contribución|)
        top_factores = sorted(
            [{"feature": k, "contribucion": v, "nombre": NOMBRES_FEATURES.get(k, k)}
             for k, v in contribuciones.items()],
            key=lambda x: abs(x["contribucion"]),
            reverse=True,
        )[:5]

        # Valores reales de las features para contexto
        valores_reales = {c: round(float(X_clean.iloc[0][c]), 3) for c in FEATURE_COLS}

        # Explicaciones
        exp_ciudadano = self._explicacion_ciudadano(top_factores, etiqueta, valores_reales)
        exp_tecnica   = self._explicacion_tecnica(top_factores, etiqueta, contribuciones)

        # Datos para gráfica de barras (Recharts)
        grafica_datos = [
            {
                "nombre": NOMBRES_FEATURES.get(f["feature"], f["feature"])[:30],
                "feature": f["feature"],
                "contribucion": round(f["contribucion"], 4),
                "color": "#EF4444" if f["contribucion"] > 0 else "#3B82F6",
            }
            for f in top_factores
        ]

        return {
            "nivel":                   etiqueta,
            "contribuciones":          {k: round(v, 4) for k, v in contribuciones.items()},
            "top_factores":            top_factores,
            "valores_reales":          valores_reales,
            "explicacion_ciudadano":   exp_ciudadano,
            "explicacion_tecnica":     exp_tecnica,
            "importancias_globales":   self.importancias_globales,
            "grafica_datos":           grafica_datos,
            "shap_disponible":         SHAP_DISPONIBLE and self.explainer is not None,
        }

    def _shap_fila(self, X_arr: np.ndarray, etiqueta: str) -> dict[str, float]:
        """Obtiene valores SHAP para una fila específica."""
        if self.explainer is None or not SHAP_DISPONIBLE:
            # Fallback: usar importancias globales con signo
            return {k: v for k, v in self.importancias_globales.items()}

        try:
            sv = self.explainer.shap_values(X_arr)

            if isinstance(sv, list):
                # Multiclase: obtener índice de la clase predicha
                try:
                    idx_clase = self.clases_modelo.index(etiqueta)
                    shap_vals = sv[idx_clase][0]
                except (ValueError, IndexError):
                    shap_vals = np.mean([c[0] for c in sv], axis=0)
            else:
                shap_vals = sv[0]

            return {
                FEATURE_COLS[i]: float(shap_vals[i])
                for i in range(min(len(FEATURE_COLS), len(shap_vals)))
            }
        except Exception as e:
            logger.warning(f"[XAI] Error calculando SHAP puntual: {e}")
            return {k: v * (1 if etiqueta == "ALTA" else -1)
                    for k, v in self.importancias_globales.items()}

    def _explicacion_ciudadano(
        self,
        top_factores: list[dict],
        etiqueta: str,
        valores_reales: dict[str, float],
    ) -> str:
        """
        Genera una explicación en lenguaje sencillo para ciudadanos.
        Sin jerga técnica. Máximo 3 factores.
        """
        nivel_texto = {
            "ALTA":  "⚠️ Riesgo territorial ALTO este período.",
            "MEDIA": "🟡 Riesgo territorial MODERADO este período.",
            "BAJA":  "✅ Condiciones territoriales FAVORABLES.",
        }.get(etiqueta, "Estado territorial calculado.")

        factores_positivos = [f for f in top_factores if f["contribucion"] > UMBRAL_SHAP_RELEVANTE]
        factores_negativos = [f for f in top_factores if f["contribucion"] < -UMBRAL_SHAP_RELEVANTE]

        partes = [nivel_texto, "Principales razones:"]

        for f in factores_positivos[:3]:
            nombre = f["nombre"]
            val = valores_reales.get(f["feature"], 0)
            if f["feature"] == "upra_var_mensual_pct" and val > 0:
                partes.append(f"📈 Los precios de insumos subieron {val:.1f}% este mes.")
            elif f["feature"] == "upra_var_mensual_pct" and val < 0:
                partes.append(f"📉 Los precios de insumos bajaron {abs(val):.1f}% este mes.")
            elif f["feature"] == "ideam_precipitacion_anomalia" and val < 0:
                partes.append(f"🌵 Déficit de lluvia: {abs(val):.0f}mm bajo lo normal.")
            elif f["feature"] == "ideam_temperatura_anomalia" and val > 0:
                partes.append(f"🌡️ Temperatura {val:.1f}°C por encima del promedio histórico.")
            elif f["feature"] == "mes":
                partes.append(f"📅 El mes {int(val)} tiene históricamente mayor vulnerabilidad.")
            else:
                partes.append(f"• {nombre}: valor actual contribuye al nivel de riesgo.")

        for f in factores_negativos[:2]:
            nombre = f["nombre"]
            partes.append(f"✓ {nombre} contribuye a reducir el riesgo.")

        if len(partes) == 2:
            partes.append("Las condiciones generales están dentro de los parámetros normales.")

        return " ".join(partes)

    def _explicacion_tecnica(
        self,
        top_factores: list[dict],
        etiqueta: str,
        contribuciones: dict[str, float],
    ) -> str:
        """Explicación detallada para investigadores y técnicos."""
        total_pos = sum(v for v in contribuciones.values() if v > 0)
        total_neg = sum(v for v in contribuciones.values() if v < 0)

        lineas = [
            f"Predicción: clase {etiqueta} (SHAP analysis).",
            f"Suma contribuciones positivas: +{total_pos:.4f} | negativas: {total_neg:.4f}",
            "Top factores por |SHAP|:",
        ]

        for i, f in enumerate(top_factores, 1):
            signo = "+" if f["contribucion"] > 0 else ""
            lineas.append(
                f"  {i}. {NOMBRES_FEATURES.get(f['feature'], f['feature'])}: "
                f"{signo}{f['contribucion']:.4f}"
            )

        return "\n".join(lineas)

    # ── Importancias globales para API ────────────────────────────────────────

    def get_importancias_api(self) -> list[dict[str, Any]]:
        """Retorna las importancias globales formateadas para el endpoint."""
        total = sum(self.importancias_globales.values()) or 1.0
        return sorted(
            [
                {
                    "feature":      k,
                    "nombre":       NOMBRES_FEATURES.get(k, k),
                    "importancia":  round(v, 4),
                    "importancia_pct": round(v / total * 100, 2),
                }
                for k, v in self.importancias_globales.items()
            ],
            key=lambda x: x["importancia"],
            reverse=True,
        )
