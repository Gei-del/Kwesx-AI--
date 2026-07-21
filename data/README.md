# Carpeta `data/` — Kwesx AI

Esta carpeta contiene los datos organizados por etapa del pipeline.

> **Nota:** Los archivos de datos reales NO se suben a git (ver `.gitignore`).
> Solo se versiona la estructura de carpetas (archivos `.gitkeep` y este README).

## Estructura

| Carpeta | Descripción | Origen |
|---------|-------------|--------|
| `01_raw/` | Datos crudos tal como vienen de la API (JSON/CSV) | Socrata API (datos.gov.co) |
| `02_external/` | Datos de referencia externos (DANE, IGAC, etc.) | Descarga manual |
| `03_processed/` | Datos limpios y normalizados | `etl/transformers/` |
| `04_feature_store/` | Features calculadas para el modelo | `ml/features.py` |
| `05_training/` | Datasets de entrenamiento (train/test split) | `ml/train.py` |
| `06_validation/` | Datasets de validación temporal | `ml/train.py` |
| `07_predictions/` | Predicciones históricas del modelo IVT | `ml/predict.py` |
| `08_exports/` | Exportaciones para visualizaciones y reportes | Manual / API |
| `09_backups/` | Backups de la base de datos PostgreSQL | `make backup` |

## Comandos útiles

```bash
# Descargar datos frescos de la API
make etl

# Descargar solo un dataset
make etl-ani
make etl-upra
make etl-ideam

# Verificar sin escribir (dry-run)
make etl-dry
```

## Convención de nombres de archivos

```
{dataset}_{YYYY-MM-DD}_{descripcion}.{ext}

Ejemplos:
  01_raw/ani_2026-07-01_peajes_raw.json
  03_processed/upra_2026-07-01_precios_clean.csv
  07_predictions/ivt_predicciones_2026-07.csv
```
