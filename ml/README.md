# Kwesx AI — Machine Learning

**Stack:** Python 3.11 · scikit-learn 1.5 · XGBoost 2.1 · SHAP 0.45 · statsmodels 0.14  
**Documentación completa:** [docs/ML.md](../docs/ML.md)

---

## Modelos

| Modelo | Archivo | Tipo |
|---|---|---|
| IVT Ensemble (RF + XGBoost) | `ensemble.py` | Clasificación (BAJA/MEDIA/ALTA) |
| Clustering Territorial | `clustering.py` | KMeans + DBSCAN |
| Forecasting | `forecasting.py` | Holt-Winters + SARIMA |
| Detección de Anomalías | `anomaly.py` | Isolation Forest + LOF |
| Explicabilidad XAI | `explainability.py` | SHAP TreeExplainer |

---

## Entrenamiento

```bash
# Requisito: datos cargados en BD (make etl primero)

make train-advanced       # Entrena todos los modelos
# o
python -m ml.train_advanced
```

Los modelos se guardan en `ml/models/*.pkl`.  
Los archivos `.pkl` están en `.gitignore` — **re-entrenar al clonar el proyecto**.

---

## Validación

```bash
make validate
# o
python -m ml.validation_report
```

Métricas objetivo: Accuracy ≥ 0.80 · F1 Macro ≥ 0.78 · AUC-ROC ≥ 0.90

---

## Estructura

```
ml/
├── ensemble.py           # IVT — VotingClassifier (RF + XGBoost)
├── clustering.py         # Segmentación territorial
├── forecasting.py        # Series temporales
├── anomaly.py            # Detección de anomalías
├── explainability.py     # SHAP values
├── features.py           # FEATURE_COLS y preparación de datos
├── train.py              # Entrenamiento básico (IVT solo)
├── train_advanced.py     # Entrenamiento de todos los modelos
├── predict.py            # Inferencia en tiempo real
├── validation_report.py  # Métricas de validación cruzada
└── models/               # Archivos .pkl (en .gitignore)
```

---

## Inferencia vía API

```bash
# IVT actual
curl http://localhost:8000/prediccion/actual

# Todos los insights ML
curl http://localhost:8000/ml/insights
```

Ver todos los endpoints ML en [docs/API.md](../docs/API.md#machine-learning-avanzado).
