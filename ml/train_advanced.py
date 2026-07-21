"""
ml/train_advanced.py
====================
Script de entrenamiento avanzado para Kwesx AI.

Entrena TODOS los modelos en el orden correcto:
  1. Features comunes (desde la API de datos.gov.co)
  2. Ensemble IVT (RF + XGBoost)
  3. Clustering territorial (KMeans + DBSCAN)
  4. Forecasting (Holt-Winters + SARIMA)
  5. Detector de anomalías (Isolation Forest + LOF)
  6. Explainability (SHAP TreeExplainer)

Uso
---
# Desde la raíz del proyecto:
python -m ml.train_advanced

# Solo modelos específicos:
python -m ml.train_advanced --modelo ensemble
python -m ml.train_advanced --modelo clustering
python -m ml.train_advanced --modelo forecasting
python -m ml.train_advanced --modelo anomaly
python -m ml.train_advanced --modelo xai

# No guardar (solo ver métricas):
python -m ml.train_advanced --dry-run

# Forzar reentrenamiento:
python -m ml.train_advanced --force
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from loguru import logger

# Configurar logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    colorize=True,
    level="INFO",
)

MODEL_DIR = Path(__file__).parent / "models"


# ─────────────────────────────────────────────────────────────────────────────
# Banner
# ─────────────────────────────────────────────────────────────────────────────

def _banner():
    logger.info("=" * 65)
    logger.info("  KWESX AI — Entrenamiento Avanzado de Modelos IA")
    logger.info("=" * 65)
    logger.info("  Modelos: Ensemble IVT | Clustering | Forecasting | Anomalías | XAI")
    logger.info("=" * 65)


# ─────────────────────────────────────────────────────────────────────────────
# Pasos de entrenamiento
# ─────────────────────────────────────────────────────────────────────────────

def _entrenar_features() -> "pd.DataFrame":  # type: ignore[name-defined]
    """Descarga y construye la matriz de features desde la API."""
    from ml.features import build_feature_matrix_from_api

    logger.info("[1/5] Construyendo features desde APIs de datos.gov.co...")
    t0 = time.time()
    df = build_feature_matrix_from_api()
    logger.success(
        f"     Features listas: {len(df)} filas × {df.shape[1]} columnas "
        f"({time.time()-t0:.1f}s)"
    )
    return df


def _entrenar_ensemble(df: "pd.DataFrame", dry_run: bool) -> dict:  # type: ignore[name-defined]
    """Entrena el Ensemble RF + XGBoost."""
    from ml.ensemble import EnsembleIVT, ENSEMBLE_PATH

    logger.info("[2/5] Entrenando Ensemble IVT (RF + XGBoost)...")
    t0 = time.time()

    modelo = EnsembleIVT()
    meta   = modelo.train(df)

    logger.success(
        f"     Ensemble OK ({time.time()-t0:.1f}s). "
        f"CV F1-macro: {meta['cv_f1_macro_mean']:.4f} ± {meta['cv_f1_macro_std']:.4f} | "
        f"RF: {meta['metricas_individuales'].get('rf_f1_macro', '?')} | "
        f"XGB: {meta['metricas_individuales'].get('xgb_f1_macro', '?')}"
    )

    _imprimir_importancias(meta.get("feature_importances", {}))

    if not dry_run:
        ruta = modelo.save()
        logger.success(f"     Guardado: {ruta}")

    return meta


def _entrenar_clustering(df: "pd.DataFrame", dry_run: bool) -> dict:  # type: ignore[name-defined]
    """Entrena KMeans + DBSCAN."""
    from ml.clustering import ClusterizadorTerritorial, CLUSTER_PATH

    logger.info("[3/5] Entrenando Clustering territorial (KMeans + DBSCAN)...")
    t0 = time.time()

    modelo  = ClusterizadorTerritorial()
    df_out  = modelo.fit_predict(df, auto_k=True)
    meta    = modelo.metadata

    km = meta.get("kmeans", {})
    db = meta.get("dbscan", {})
    logger.success(
        f"     Clustering OK ({time.time()-t0:.1f}s). "
        f"KMeans: {km.get('n_clusters','?')} clústeres "
        f"(silhouette={km.get('silhouette','?')}) | "
        f"DBSCAN: {db.get('n_clusters','?')} grupos + {db.get('n_outliers','?')} outliers"
    )

    logger.info("     Perfiles territoriales detectados:")
    for pid, perfil in modelo.perfiles.items():
        logger.info(
            f"       Perfil {pid}: {perfil['nombre']} "
            f"({perfil['n_periodos']} períodos)"
        )

    if not dry_run:
        ruta = modelo.save()
        logger.success(f"     Guardado: {ruta}")

    return meta


def _entrenar_forecasting(df: "pd.DataFrame", dry_run: bool) -> dict:  # type: ignore[name-defined]
    """Entrena modelos de series temporales."""
    from ml.forecasting import ForecastingTerritorial, FORECAST_PATH

    logger.info("[4/5] Entrenando Forecasting (Holt-Winters + SARIMA)...")
    t0 = time.time()

    modelo = ForecastingTerritorial()
    meta   = modelo.train(df)

    series_ok = list(modelo.historicos.keys())
    logger.success(
        f"     Forecasting OK ({time.time()-t0:.1f}s). "
        f"Series ajustadas: {series_ok}"
    )

    # Mostrar RMSE por serie
    for serie, m in meta.get("metricas", {}).items():
        hw_rmse = m.get("metricas_hw", {}).get("rmse", "?")
        ar_rmse = m.get("metricas_arima", {}).get("rmse", "?")
        logger.info(
            f"       {serie}: HW RMSE={hw_rmse} | ARIMA RMSE={ar_rmse} "
            f"({m.get('n_puntos','?')} puntos)"
        )

    # Demo: forecast para UPRA (6 meses)
    try:
        forecast_demo = modelo.forecast("upra_indice_total", horizonte=6)
        cambio = forecast_demo.get("cambio_esperado_pct", 0)
        logger.info(
            f"     Demo UPRA 6 meses: cambio esperado {cambio:+.1f}% | "
            f"{forecast_demo.get('interpretacion','')[:60]}..."
        )
    except Exception as e:
        logger.warning(f"     Demo forecast falló: {e}")

    if not dry_run:
        ruta = modelo.save()
        logger.success(f"     Guardado: {ruta}")

    return meta


def _entrenar_anomaly(df: "pd.DataFrame", dry_run: bool) -> dict:  # type: ignore[name-defined]
    """Entrena el detector de anomalías."""
    from ml.anomaly import DetectorAnomalias, ANOMALY_PATH

    logger.info("[5/5] Entrenando Detector de Anomalías (IsoForest + LOF)...")
    t0 = time.time()

    modelo = DetectorAnomalias(contamination=0.10)
    meta   = modelo.fit(df)

    logger.success(
        f"     Detector OK ({time.time()-t0:.1f}s). "
        f"{meta['n_muestras']} muestras, contaminación {meta['contamination']}"
    )

    # Detección inmediata sobre los datos de entrenamiento
    try:
        resultado = modelo.detectar(df)
        logger.info(
            f"     Anomalías en datos históricos: "
            f"{resultado['n_anomalias']} ({resultado['tasa_anomalia_pct']}%) | "
            f"{resultado['interpretacion'][:60]}..."
        )
    except Exception as e:
        logger.warning(f"     Detección demo falló: {e}")

    if not dry_run:
        ruta = modelo.save()
        logger.success(f"     Guardado: {ruta}")

    return meta


def _entrenar_xai(df: "pd.DataFrame", dry_run: bool) -> None:
    """Entrena el Explainability (SHAP). Requiere que el ensemble esté guardado."""
    from ml.ensemble import EnsembleIVT, ENSEMBLE_PATH
    from ml.explainability import ExplicadorIVT
    from ml.features import FEATURE_COLS
    from ml.modelo_territorial import compute_ivt_score, score_to_label, LABELS

    xai_path = Path(__file__).parent / "models" / "xai_explainer.pkl"

    if not ENSEMBLE_PATH.exists() and not dry_run:
        logger.warning("[XAI] Ensemble no encontrado. Saltando XAI.")
        return

    logger.info("[XAI] Iniciando Explainability con SHAP...")
    t0 = time.time()

    try:
        import joblib

        # Cargar el ensemble
        ensemble = EnsembleIVT()
        if ENSEMBLE_PATH.exists():
            ensemble.load()
        else:
            meta = ensemble.train(df)

        X_train = df[FEATURE_COLS].fillna(0.0)

        # Inicializar explainer
        explicador = ExplicadorIVT()
        explicador.fit(
            pipeline=ensemble.pipeline,
            X_train=X_train,
            class_names=list(LABELS.values()),
        )

        logger.success(
            f"     XAI OK ({time.time()-t0:.1f}s). "
            f"Top importancias: "
            + ", ".join(
                f"{k}={v:.4f}"
                for k, v in sorted(
                    explicador.importancias_globales.items(),
                    key=lambda x: x[1], reverse=True
                )[:3]
            )
        )

        if not dry_run:
            joblib.dump(explicador, xai_path)
            logger.success(f"     XAI guardado: {xai_path}")

    except Exception as e:
        logger.warning(f"[XAI] No se pudo entrenar SHAP: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────────────────────────────────────

def _imprimir_importancias(importancias: dict[str, float], top_n: int = 5) -> None:
    """Imprime un ranking visual de importancias de features."""
    if not importancias:
        return
    logger.info("     Importancias de features (top 5):")
    for feat, imp in sorted(importancias.items(), key=lambda x: x[1], reverse=True)[:top_n]:
        bar = "█" * int(imp * 30)
        logger.info(f"       {feat:44s}  {imp:.4f}  {bar}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Kwesx AI — Entrenamiento avanzado de modelos IA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--modelo",
        choices=["all", "ensemble", "clustering", "forecasting", "anomaly", "xai"],
        default="all",
        help="Modelo a entrenar (default: all)",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo mostrar métricas, no guardar modelos")
    parser.add_argument("--force", action="store_true",
                        help="Reentrenar aunque los modelos ya existan")
    args = parser.parse_args()

    _banner()
    t_inicio = time.time()

    # ── 1. Features (siempre necesarias) ────────────────────────────────────
    try:
        df = _entrenar_features()
    except Exception as e:
        logger.error(f"Error fatal al construir features: {e}")
        sys.exit(1)

    errores: list[str] = []

    # ── 2. Ensemble ──────────────────────────────────────────────────────────
    if args.modelo in ("all", "ensemble"):
        try:
            _entrenar_ensemble(df, args.dry_run)
        except Exception as e:
            logger.error(f"[Ensemble] Error: {e}")
            errores.append(f"ensemble: {e}")

    # ── 3. Clustering ────────────────────────────────────────────────────────
    if args.modelo in ("all", "clustering"):
        try:
            _entrenar_clustering(df, args.dry_run)
        except Exception as e:
            logger.error(f"[Clustering] Error: {e}")
            errores.append(f"clustering: {e}")

    # ── 4. Forecasting ───────────────────────────────────────────────────────
    if args.modelo in ("all", "forecasting"):
        try:
            _entrenar_forecasting(df, args.dry_run)
        except Exception as e:
            logger.error(f"[Forecasting] Error: {e}")
            errores.append(f"forecasting: {e}")

    # ── 5. Anomaly ───────────────────────────────────────────────────────────
    if args.modelo in ("all", "anomaly"):
        try:
            _entrenar_anomaly(df, args.dry_run)
        except Exception as e:
            logger.error(f"[Anomaly] Error: {e}")
            errores.append(f"anomaly: {e}")

    # ── 6. XAI (depende del ensemble) ────────────────────────────────────────
    if args.modelo in ("all", "xai"):
        try:
            _entrenar_xai(df, args.dry_run)
        except Exception as e:
            logger.error(f"[XAI] Error: {e}")
            errores.append(f"xai: {e}")

    # ── Resumen final ────────────────────────────────────────────────────────
    total_tiempo = time.time() - t_inicio
    logger.info("")
    logger.info("=" * 65)
    if errores:
        logger.warning(f"Entrenamiento completado con {len(errores)} error(es) en {total_tiempo:.1f}s:")
        for e in errores:
            logger.warning(f"  ✗ {e}")
    else:
        logger.success(f"✅ Entrenamiento completo en {total_tiempo:.1f}s. Todos los modelos OK.")

    if not args.dry_run:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        modelos_guardados = list(MODEL_DIR.glob("*.pkl"))
        logger.info(f"   Modelos guardados: {len(modelos_guardados)} archivos en {MODEL_DIR}")
        for m in modelos_guardados:
            size_kb = m.stat().st_size // 1024
            logger.info(f"   → {m.name} ({size_kb} KB)")
    logger.info("=" * 65)


if __name__ == "__main__":
    main()
