"""
ml/ensemble.py
==============
Ensemble IVT: Random Forest + XGBoost con votación ponderada.

Arquitectura
------------
- Base Classifier 1: Random Forest (calibrado con CalibratedClassifierCV)
- Base Classifier 2: XGBoost Classifier (calibrado)
- Ensemble: VotingClassifier (soft voting, pesos 0.45 RF / 0.55 XGBoost)
- Output: Clase BAJA/MEDIA/ALTA + probabilidades calibradas + intervalo confianza

El XGBoost captura interacciones no lineales que el RF pierde;
la combinación reduce varianza y mejora la calibración de probabilidades.

Uso
---
    from ml.ensemble import EnsembleIVT
    modelo = EnsembleIVT()
    metricas = modelo.train(df_features)
    resultado = modelo.predict(X)
    modelo.save()

Compatibilidad
--------------
La API de predict() tiene la misma firma que ModeloTerritorial,
por lo que puede reemplazarlo en cualquier endpoint sin cambios.
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
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBClassifier

from ml.features import FEATURE_COLS
from ml.modelo_territorial import (
    LABELS,
    LABEL_COLORS,
    THRESHOLD_ALTA,
    THRESHOLD_MEDIA,
    compute_ivt_score,
    score_to_label,
)

# ─────────────────────────────────────────────────────────────────────────────
# Rutas
# ─────────────────────────────────────────────────────────────────────────────

MODEL_DIR       = Path(__file__).parent / "models"
ENSEMBLE_PATH   = MODEL_DIR / "ivt_ensemble.pkl"
ENSEMBLE_META   = MODEL_DIR / "ivt_ensemble_metadata.json"


# ─────────────────────────────────────────────────────────────────────────────
# Clase principal
# ─────────────────────────────────────────────────────────────────────────────

class EnsembleIVT:
    """
    Ensemble RF + XGBoost para clasificación de vulnerabilidad territorial.

    Mejoras vs ModeloTerritorial (solo RF):
    - XGBoost captura interacciones profundas entre features
    - Votación ponderada reduce la varianza del RF en datasets pequeños
    - Calibración con Platt scaling → probabilidades más confiables
    - Reporte comparativo entre los 2 clasificadores base
    """

    def __init__(self):
        self.pipeline: Pipeline | None = None
        self.label_encoder = LabelEncoder()
        self.metadata: dict[str, Any] = {}
        self.metricas_individuales: dict[str, Any] = {}

    # ── Construcción del pipeline ─────────────────────────────────────────────

    def _build_rf(self) -> RandomForestClassifier:
        return RandomForestClassifier(
            n_estimators=400,
            max_depth=8,
            min_samples_leaf=2,
            max_features="sqrt",
            class_weight="balanced",
            random_state=2026,
            n_jobs=-1,
        )

    def _build_xgb(self, n_clases: int) -> XGBClassifier:
        return XGBClassifier(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.8,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.5,
            use_label_encoder=False,
            eval_metric="mlogloss",
            num_class=n_clases,
            objective="multi:softprob",
            random_state=2026,
            n_jobs=-1,
        )

    def _build_pipeline(self, n_clases: int) -> Pipeline:
        rf  = CalibratedClassifierCV(self._build_rf(),  cv=3, method="isotonic")
        xgb = CalibratedClassifierCV(self._build_xgb(n_clases), cv=3, method="sigmoid")

        ensemble = VotingClassifier(
            estimators=[("rf", rf), ("xgb", xgb)],
            voting="soft",
            weights=[0.45, 0.55],   # XGBoost peso levemente mayor (más estable en tabular)
            n_jobs=1,               # VotingClassifier no paraleliza bien con n_jobs>1
        )

        return Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", ensemble),
        ])

    # ── Entrenamiento ─────────────────────────────────────────────────────────

    def train(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Entrena el ensemble con los features del DataFrame.

        Pasos:
          1. Generar targets IVT con compute_ivt_score()
          2. Verificar distribución de clases
          3. Train/test split estratificado
          4. Entrenar RF y XGBoost individualmente para métricas comparativas
          5. Entrenar ensemble final
          6. Cross-validation 5-fold con F1-macro
          7. Guardar metadatos
        """
        if len(df) < 15:
            raise ValueError(f"Datos insuficientes para ensemble: {len(df)} filas (mínimo 15).")

        logger.info(f"[Ensemble] Iniciando entrenamiento con {len(df)} observaciones...")

        # ── 1. Targets ──────────────────────────────────────────────────────
        scores = compute_ivt_score(df)
        labels_int = scores.apply(score_to_label)

        clases = sorted(labels_int.unique())
        dist_str = " | ".join(f"{LABELS[c]}: {(labels_int == c).sum()}" for c in clases)
        logger.info(f"[Ensemble] Distribución: {dist_str}")

        if len(clases) < 2:
            raise ValueError("Solo hay 1 clase. Verifica compute_ivt_score y thresholds.")

        # Labels como strings para VotingClassifier
        y_str = labels_int.map(LABELS)

        X = df[FEATURE_COLS].fillna(0.0)

        # ── 2. Train/test split ──────────────────────────────────────────────
        min_samples = y_str.value_counts().min()
        do_stratify = len(df) >= 20 and min_samples >= 2

        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y_str,
            test_size=0.2,
            random_state=2026,
            stratify=y_str if do_stratify else None,
        )

        # ── 3. Métricas individuales (RF y XGBoost por separado) ─────────────
        self.metricas_individuales = self._train_base_models(X_tr, X_te, y_tr, y_te, len(clases))

        # ── 4. Ensemble final ────────────────────────────────────────────────
        self.pipeline = self._build_pipeline(len(clases))
        self.pipeline.fit(X_tr, y_tr)

        # ── 5. Evaluación ensemble ───────────────────────────────────────────
        y_pred = self.pipeline.predict(X_te)
        clases_test = sorted(y_te.unique())
        report = classification_report(
            y_te, y_pred,
            labels=clases_test,
            output_dict=True,
            zero_division=0,
        )

        # ── 6. Cross-validation ──────────────────────────────────────────────
        cv_folds = max(2, min(5, min_samples))
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=2026)
        cv_scores = cross_val_score(self.pipeline, X, y_str, cv=cv, scoring="f1_macro")

        # ── 7. Importancias (extraemos del RF dentro del ensemble) ───────────
        try:
            voting_clf = self.pipeline.named_steps["classifier"]
            rf_calibrated = voting_clf.estimators_[0]   # CalibratedClassifierCV
            rf_base = rf_calibrated.calibrated_classifiers_[0].estimator
            importances = dict(zip(FEATURE_COLS, rf_base.feature_importances_.round(4)))
        except Exception:
            importances = {f: round(1 / len(FEATURE_COLS), 4) for f in FEATURE_COLS}

        self.metadata = {
            "modelo":               "EnsembleIVT (RF 0.45 + XGBoost 0.55)",
            "n_train":              len(X_tr),
            "n_test":               len(X_te),
            "cv_folds":             cv_folds,
            "cv_f1_macro_mean":     round(float(cv_scores.mean()), 4),
            "cv_f1_macro_std":      round(float(cv_scores.std()), 4),
            "accuracy_test":        round(float(report.get("accuracy", 0)), 4),
            "f1_macro_test":        round(float(report.get("macro avg", {}).get("f1-score", 0)), 4),
            "clases":               [LABELS[c] for c in clases],
            "distribucion":         {LABELS[c]: int((labels_int == c).sum()) for c in clases},
            "thresholds":           {"media": THRESHOLD_MEDIA, "alta": THRESHOLD_ALTA},
            "feature_importances":  importances,
            "metricas_individuales":self.metricas_individuales,
            "entrenado_en":         datetime.now().isoformat(),
        }

        logger.success(
            f"[Ensemble] Entrenamiento OK. "
            f"CV F1-macro ({cv_folds}-fold): {cv_scores.mean():.3f} ± {cv_scores.std():.3f} | "
            f"F1-macro test: {self.metadata['f1_macro_test']:.3f} | "
            f"vs RF solo: {self.metricas_individuales.get('rf_f1_macro', 0):.3f} | "
            f"vs XGB solo: {self.metricas_individuales.get('xgb_f1_macro', 0):.3f}"
        )
        return self.metadata

    def _train_base_models(
        self,
        X_tr: pd.DataFrame, X_te: pd.DataFrame,
        y_tr: pd.Series, y_te: pd.Series,
        n_clases: int,
    ) -> dict[str, float]:
        """Entrena RF y XGBoost por separado para obtener métricas comparativas."""
        metricas: dict[str, float] = {}
        scaler = StandardScaler()
        X_tr_s = scaler.fit_transform(X_tr)
        X_te_s = scaler.transform(X_te)

        # RF solo
        try:
            rf = self._build_rf()
            rf.fit(X_tr_s, y_tr)
            y_rf = rf.predict(X_te_s)
            metricas["rf_f1_macro"] = round(float(f1_score(y_te, y_rf, average="macro", zero_division=0)), 4)
            metricas["rf_accuracy"] = round(float((y_rf == y_te).mean()), 4)
        except Exception as e:
            logger.warning(f"[Ensemble] RF individual error: {e}")

        # XGBoost solo
        try:
            le = LabelEncoder()
            y_tr_enc = le.fit_transform(y_tr)
            y_te_enc = le.transform(y_te)
            xgb = self._build_xgb(n_clases)
            xgb.fit(X_tr_s, y_tr_enc)
            y_xgb = le.inverse_transform(xgb.predict(X_te_s))
            metricas["xgb_f1_macro"] = round(float(f1_score(y_te, y_xgb, average="macro", zero_division=0)), 4)
            metricas["xgb_accuracy"] = round(float((y_xgb == y_te).mean()), 4)
        except Exception as e:
            logger.warning(f"[Ensemble] XGB individual error: {e}")

        return metricas

    # ── Predicción ─────────────────────────────────────────────────────────────

    def predict(self, X: pd.DataFrame) -> dict[str, Any]:
        """Predice el IVT para una fila de features."""
        if self.pipeline is None:
            raise RuntimeError("Ensemble no entrenado. Ejecuta train() o load() primero.")

        X_clean = X[FEATURE_COLS].fillna(0.0)
        etiqueta = str(self.pipeline.predict(X_clean)[0])
        probas   = self.pipeline.predict_proba(X_clean)[0]

        # Mapear clases del VotingClassifier al orden BAJA/MEDIA/ALTA
        clases_modelo = list(self.pipeline.named_steps["classifier"].classes_)
        proba_dict = {c: 0.0 for c in LABELS.values()}
        for i, c in enumerate(clases_modelo):
            proba_dict[str(c)] = round(float(probas[i]), 4)

        # Clase numérica para compatibilidad con código existente
        clase_int = next((k for k, v in LABELS.items() if v == etiqueta), 0)

        # Nivel de confianza: probabilidad de la clase predicha
        confianza = proba_dict.get(etiqueta, 0.0)
        if confianza >= 0.75:
            nivel_confianza = "Alta"
        elif confianza >= 0.50:
            nivel_confianza = "Media"
        else:
            nivel_confianza = "Baja"

        return {
            "clase":             clase_int,
            "etiqueta":          etiqueta,
            "probabilidades":    proba_dict,
            "confianza":         round(confianza, 4),
            "nivel_confianza":   nivel_confianza,
            "color":             LABEL_COLORS.get(clase_int, "#888"),
            "modelo":            "Ensemble RF + XGBoost",
        }

    # ── Persistencia ──────────────────────────────────────────────────────────

    def save(self) -> str:
        if self.pipeline is None:
            raise RuntimeError("Nada que guardar.")
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump({"pipeline": self.pipeline, "metadata": self.metadata}, ENSEMBLE_PATH)
        with open(ENSEMBLE_META, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        logger.success(f"[Ensemble] Guardado en {ENSEMBLE_PATH}")
        return str(ENSEMBLE_PATH)

    def load(self) -> "EnsembleIVT":
        if not ENSEMBLE_PATH.exists():
            raise FileNotFoundError(
                f"Ensemble no encontrado en {ENSEMBLE_PATH}. "
                "Ejecuta: python -m ml.train_advanced"
            )
        data = joblib.load(ENSEMBLE_PATH)
        self.pipeline = data["pipeline"]
        self.metadata = data.get("metadata", {})
        logger.info(f"[Ensemble] Cargado desde {ENSEMBLE_PATH}")
        return self

    def is_trained(self) -> bool:
        return ENSEMBLE_PATH.exists()
