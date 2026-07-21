"""
ml/train.py
===========
Script de entrenamiento del modelo IVT de Kwesx AI.

Corre el pipeline completo:
  1. Descarga datos de las APIs de datos.gov.co (UPRA + IDEAM)
  2. Construye la matriz de features cruzando las 3 fuentes
  3. Genera los targets con la función de scoring IVT
  4. Entrena el Random Forest Classifier
  5. Evalúa con cross-validation
  6. Guarda el modelo en ml/models/ivt_model.pkl

Uso
---
# Desde la raíz del proyecto:
python -m ml.train

# Ver resultado sin guardar:
python -m ml.train --dry-run

# Forzar reentrenamiento aunque ya exista el modelo:
python -m ml.train --force
"""

import argparse
import json
import sys
from pathlib import Path
from loguru import logger

# Logging formato limpio para el entrenamiento
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
    colorize=True,
)


def main():
    parser = argparse.ArgumentParser(description="Entrenar el modelo IVT de Kwesx AI")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostrar métricas sin guardar el modelo")
    parser.add_argument("--force", action="store_true",
                        help="Reentrenar aunque el modelo ya exista")
    args = parser.parse_args()

    from ml.modelo_territorial import ModeloTerritorial, MODEL_PATH
    from ml.features import build_feature_matrix_from_api, FEATURE_COLS

    # Verificar si ya existe el modelo
    if MODEL_PATH.exists() and not args.force and not args.dry_run:
        logger.info(f"Modelo ya existe en {MODEL_PATH}. Usa --force para reentrenar.")
        return

    logger.info("=" * 60)
    logger.info("Kwesx AI — Entrenamiento del Modelo IVT")
    logger.info("=" * 60)

    # 1. Construir features desde la API
    logger.info("Paso 1/3: Descargando y construyendo features...")
    try:
        df = build_feature_matrix_from_api()
    except Exception as e:
        logger.error(f"Error al construir features: {e}")
        sys.exit(1)

    logger.info(f"Features disponibles: {len(df)} meses")
    logger.info(f"Período: {df['fecha'].min().date()} → {df['fecha'].max().date()}")
    logger.info(f"Columnas: {list(df.columns)}")

    # Verificar que tenemos las features requeridas
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        logger.error(f"Faltan columnas requeridas: {missing}")
        sys.exit(1)

    # 2. Entrenar
    logger.info("Paso 2/3: Entrenando Random Forest Classifier...")
    modelo = ModeloTerritorial()
    try:
        metricas = modelo.train(df)
    except Exception as e:
        logger.error(f"Error durante el entrenamiento: {e}")
        sys.exit(1)

    # 3. Reportar métricas
    logger.info("")
    logger.info("=" * 60)
    logger.info("MÉTRICAS DEL MODELO")
    logger.info("=" * 60)
    logger.info(f"  Datos de entrenamiento: {metricas['n_train']} meses")
    logger.info(f"  Datos de evaluación:    {metricas['n_test']} meses")
    logger.info(f"  CV F1-macro (5-fold):   {metricas['cv_f1_mean']:.4f} ± {metricas['cv_f1_std']:.4f}")
    logger.info(f"  Accuracy test:          {metricas['accuracy']:.4f}")
    logger.info("")
    logger.info("  Importancia de features:")
    sorted_imp = sorted(
        metricas["feature_importances"].items(),
        key=lambda x: x[1], reverse=True
    )
    for feat, imp in sorted_imp[:5]:
        bar = "█" * int(imp * 40)
        logger.info(f"    {feat:45s} {imp:.4f} {bar}")

    # 4. Guardar (si no es dry-run)
    if args.dry_run:
        logger.info("")
        logger.info("Modo dry-run: modelo NO guardado.")
    else:
        logger.info("")
        logger.info("Paso 3/3: Guardando modelo...")
        ruta = modelo.save()
        logger.success(f"Modelo guardado en: {ruta}")

        # Guardar metadata como JSON para referencia
        meta_path = Path(ruta).parent / "ivt_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metricas, f, indent=2, ensure_ascii=False)
        logger.success(f"Metadata guardada en: {meta_path}")

    logger.info("")
    logger.success("Entrenamiento completado.")


if __name__ == "__main__":
    main()
