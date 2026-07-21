"""
ml/modelo_territorial.py
========================
Modelo de IA para el Indice de Vulnerabilidad Territorial (IVT) de Kwesx AI.

Clasifica cada periodo en 3 niveles:
  - BAJA  (0): precios estables, clima normal
  - MEDIA (1): senales de alerta en 1-2 indicadores
  - ALTA  (2): presion alta en precios + anomalia climatica severa

Formula del IVT score (0 a 100):
  IVT = 0.40 x Presion_UPRA + 0.35 x Anomalia_Climatica + 0.25 x Factor_Temporal

Umbrales calibrados para la distribucion real de datos UPRA 2018-2026:
  BAJA:  IVT < 25
  MEDIA: 25 <= IVT < 42
  ALTA:  IVT >= 42

Nota sobre los umbrales
------------------------
Con datos IDEAM sinteticos (sin anomalias reales), el componente climatico
aporta ~0 al score. Los umbrales se calibraron para que la distribucion
de clases con los 89 meses de UPRA sea aproximadamente 45% / 35% / 20%,
lo que da suficientes ejemplos de ALTA para entrenar un clasificador robusto.
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from loguru import logger
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report

from ml.features import FEATURE_COLS

# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

MODEL_DIR  = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "ivt_model.pkl"
METADATA_PATH = MODEL_DIR / "ivt_metadata.json"

LABELS       = {0: "BAJA", 1: "MEDIA", 2: "ALTA"}
LABEL_COLORS = {0: "#3FA796", 1: "#F2A541", 2: "#C0392B"}

# Umbrales calibrados (ajustados para generar 3 clases con datos reales UPRA)
THRESHOLD_MEDIA = 25.0
THRESHOLD_ALTA  = 42.0


# ─────────────────────────────────────────────────────────────────────────────
# Funcion de scoring (genera los targets de entrenamiento)
# ─────────────────────────────────────────────────────────────────────────────

def compute_ivt_score(df: pd.DataFrame) -> pd.Series:
    """
    Calcula el Indice de Vulnerabilidad Territorial (IVT) como score 0-100.

    Componentes
    -----------
    1. Presion UPRA (40%):
       - Indice total normalizado al rango historico 2018-2026
       - Penaliza variaciones mensuales positivas (subidas de precio)

    2. Anomalia climatica (35%):
       - Sequia: precipitacion muy baja vs normal -> riesgo alto
       - Calor extremo: temperatura elevada -> riesgo moderado
       (Con datos sinteticos este componente es ~0; con datos reales amplifica)

    3. Factor temporal (25%):
       - Meses de cosecha (sep-nov): vulnerabilidad critica
       - Anos de alta inflacion 2022-2023: penalizacion adicional
       - Anos post-inflacion 2024-2025: penalizacion leve
    """
    n = len(df)
    idx = df.index

    # ── 1. Componente UPRA (40%) ──────────────────────────────────────────
    idx_min = df["upra_indice_total"].min()
    idx_max = df["upra_indice_total"].max()

    if idx_max > idx_min:
        upra_norm = (df["upra_indice_total"] - idx_min) / (idx_max - idx_min)
    else:
        upra_norm = pd.Series(0.5, index=idx)

    # Variacion mensual: positiva = presion al alza (mala); negativa = alivio
    var_clip = df["upra_var_mensual_pct"].clip(-5, 10)
    var_norm = (var_clip + 5) / 15   # rango -5..10 -> 0..1

    upra_component = (0.55 * upra_norm + 0.45 * var_norm) * 100 * 0.40

    # ── 2. Componente climatico (35%) ─────────────────────────────────────
    prec_anom = df["ideam_precipitacion_anomalia"]
    drought_score = np.maximum(0.0, -prec_anom / 120).clip(0, 1)
    flood_score   = (np.maximum(0.0, prec_anom / 250) * 0.4).clip(0, 0.4)
    prec_risk = (drought_score + flood_score).clip(0, 1)

    temp_anom  = df["ideam_temperatura_anomalia"]
    temp_risk  = np.maximum(0.0, temp_anom / 2.5).clip(0, 1)

    clima_component = (0.65 * prec_risk + 0.35 * temp_risk) * 100 * 0.35

    # ── 3. Factor temporal (25%) ──────────────────────────────────────────
    # Meses de cosecha en Colombia: sep-nov (mayor demanda de insumos)
    cosecha = df["mes"].isin([9, 10, 11]).astype(float) * 22

    # Penalizacion por periodos de alta inflacion agricola colombiana
    inflacion = pd.Series(0.0, index=idx)
    inflacion = inflacion.where(~df["anio"].isin([2022, 2023]), 28)  # pico inflacion
    inflacion = inflacion.where(~df["anio"].isin([2024, 2025]), 12)  # normalizacion parcial

    temporal_component = np.minimum(100.0, cosecha + inflacion) * 0.25

    score = upra_component + clima_component + temporal_component
    return score.clip(0, 100).round(2)


def score_to_label(score: float) -> int:
    """Convierte el IVT score (0-100) a clase (0=BAJA, 1=MEDIA, 2=ALTA)."""
    if score >= THRESHOLD_ALTA:
        return 2
    elif score >= THRESHOLD_MEDIA:
        return 1
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Modelo
# ─────────────────────────────────────────────────────────────────────────────

class ModeloTerritorial:
    """Wrapper del modelo IVT (Pipeline sklearn: StandardScaler + RandomForest)."""

    def __init__(self):
        self.pipeline: Pipeline | None = None
        self.feature_importances_: dict | None = None
        self.metadata: dict = {}

    def build_pipeline(self) -> Pipeline:
        return Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", RandomForestClassifier(
                n_estimators=300,
                max_depth=8,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=2026,
                n_jobs=-1,
            )),
        ])

    def train(self, df: pd.DataFrame) -> dict:
        """
        Entrena el modelo Random Forest con los datos de features.

        Pasos:
          1. Genera targets con compute_ivt_score()
          2. Verifica que haya al menos 2 clases
          3. Split train/test (80/20, estratificado si es posible)
          4. Entrena, evalua con CV y guarda importancias
        """
        if len(df) < 10:
            raise ValueError(f"Datos insuficientes: {len(df)} filas (minimo 10).")

        logger.info(f"[Modelo] Entrenando con {len(df)} observaciones...")

        # Generar targets
        ivt_scores = compute_ivt_score(df)
        labels     = ivt_scores.apply(score_to_label)

        clases_presentes = sorted(labels.unique())
        dist_str = " | ".join(
            f"{LABELS[c]}: {(labels == c).sum()}" for c in clases_presentes
        )
        logger.info(f"[Modelo] Distribucion de clases: {dist_str}")

        if len(clases_presentes) < 2:
            raise ValueError(
                "Solo hay 1 clase en los datos. "
                "Verifica la funcion compute_ivt_score y los umbrales."
            )

        X = df[FEATURE_COLS].fillna(0)
        y = labels

        # Train/test split — estratificado solo si todas las clases tienen >= 2 muestras
        min_samples_por_clase = y.value_counts().min()
        do_stratify = (len(df) >= 20 and min_samples_por_clase >= 2)

        if len(df) >= 20:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=0.2,
                random_state=2026,
                stratify=y if do_stratify else None,
            )
        else:
            X_train, X_test = X, X
            y_train, y_test = y, y

        # Entrenar
        self.pipeline = self.build_pipeline()
        self.pipeline.fit(X_train, y_train)

        # Evaluacion — usar solo las clases que realmente aparecen en test
        y_pred = self.pipeline.predict(X_test)
        clases_test = sorted(y_test.unique())
        nombres_test = [LABELS[c] for c in clases_test]

        report = classification_report(
            y_test, y_pred,
            labels=clases_test,
            target_names=nombres_test,
            output_dict=True,
            zero_division=0,
        )

        # Cross-validation (5-fold o n_samples si hay pocos datos)
        cv_folds = min(5, min_samples_por_clase, len(df) // 5)
        cv_folds = max(cv_folds, 2)
        cv_scores = cross_val_score(self.pipeline, X, y, cv=cv_folds, scoring="f1_macro")

        # Importancia de features
        rf = self.pipeline.named_steps["classifier"]
        self.feature_importances_ = dict(
            zip(FEATURE_COLS, rf.feature_importances_.round(4))
        )

        self.metadata = {
            "n_train":              len(X_train),
            "n_test":               len(X_test),
            "cv_folds":             cv_folds,
            "cv_f1_mean":           round(cv_scores.mean(), 4),
            "cv_f1_std":            round(cv_scores.std(), 4),
            "accuracy":             round(report.get("accuracy", 0), 4),
            "clases_presentes":     [LABELS[c] for c in clases_presentes],
            "distribucion":         {LABELS[c]: int((labels == c).sum()) for c in clases_presentes},
            "feature_importances":  self.feature_importances_,
            "thresholds":           {"media": THRESHOLD_MEDIA, "alta": THRESHOLD_ALTA},
            "labels":               {str(k): v for k, v in LABELS.items()},
        }

        logger.success(
            f"[Modelo] Entrenamiento OK. "
            f"CV F1-macro ({cv_folds}-fold): {cv_scores.mean():.3f} +/- {cv_scores.std():.3f} | "
            f"Accuracy test: {report.get('accuracy', 0):.3f} | "
            f"Clases: {[LABELS[c] for c in clases_presentes]}"
        )
        return self.metadata

    def predict(self, X: pd.DataFrame) -> dict:
        """Predice el IVT para un DataFrame de features."""
        if self.pipeline is None:
            raise RuntimeError("Modelo no entrenado. Ejecuta train() o load() primero.")

        X_clean = X[FEATURE_COLS].fillna(0)
        clase = int(self.pipeline.predict(X_clean)[0])
        proba = self.pipeline.predict_proba(X_clean)[0]

        # predict_proba devuelve solo las clases vistas en training
        clases_modelo = list(self.pipeline.named_steps["classifier"].classes_)
        proba_dict = {}
        for i, c in enumerate(clases_modelo):
            proba_dict[LABELS[c]] = round(float(proba[i]), 4)
        # Asegurar que las 3 etiquetas siempre aparezcan en la respuesta
        for label in LABELS.values():
            if label not in proba_dict:
                proba_dict[label] = 0.0

        return {
            "clase":          clase,
            "etiqueta":       LABELS[clase],
            "probabilidades": proba_dict,
            "color":          LABEL_COLORS[clase],
        }

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Predice para multiples filas."""
        if self.pipeline is None:
            raise RuntimeError("Modelo no cargado.")

        X = df[FEATURE_COLS].fillna(0)
        clases = self.pipeline.predict(X)

        df = df.copy()
        df["ivt_clase"]    = clases
        df["ivt_etiqueta"] = [LABELS[c] for c in clases]
        return df

    def save(self) -> str:
        if self.pipeline is None:
            raise RuntimeError("No hay modelo para guardar.")
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump({"pipeline": self.pipeline, "metadata": self.metadata}, MODEL_PATH)
        # Escribir metadata separada en JSON (para el endpoint /prediccion/metadata)
        import json
        from datetime import datetime
        meta_out = {**self.metadata, "entrenado_en": datetime.now().isoformat()}
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(meta_out, f, ensure_ascii=False, indent=2)
        logger.success(f"[Modelo] Guardado en {MODEL_PATH}")
        logger.success(f"[Modelo] Metadata JSON guardado en {METADATA_PATH}")
        return str(MODEL_PATH)

    def load(self) -> "ModeloTerritorial":
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Modelo no encontrado en {MODEL_PATH}. "
                "Ejecuta primero: python -m ml.train"
            )
        data = joblib.load(MODEL_PATH)
        self.pipeline = data["pipeline"]
        self.metadata = data.get("metadata", {})
        logger.info(f"[Modelo] Cargado desde {MODEL_PATH}")
        return self

    def is_trained(self) -> bool:
        return MODEL_PATH.exists()
