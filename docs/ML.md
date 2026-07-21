# Kwesx AI — Documentación de Machine Learning

**Stack ML:** Python 3.11 · scikit-learn 1.5 · XGBoost 2.1 · SHAP 0.45 · statsmodels 0.14

---

## Modelos implementados

### 1. Modelo IVT — Índice de Vulnerabilidad Territorial

**Archivo:** `ml/ensemble.py`  
**Tipo:** Clasificación multiclase (3 clases: BAJA / MEDIA / ALTA)

#### Arquitectura
```
VotingClassifier (soft voting)
  ├── RandomForestClassifier    (peso: 0.45)
  └── XGBClassifier             (peso: 0.55)
```

#### Features de entrada (FEATURE_COLS)
```python
[
  "upra_indice_total",        # Índice total de precios UPRA
  "upra_var_mensual_pct",     # Variación mensual %
  "upra_fertilizantes",       # Subíndice fertilizantes
  "upra_plaguicidas",         # Subíndice plaguicidas
  "ideam_precipitacion_mm",   # Precipitación mensual en mm
  "ideam_precipitacion_anomalia", # Desviación del promedio histórico
  "ideam_temperatura_c",      # Temperatura promedio °C
  "ideam_temperatura_anomalia",   # Desviación de temperatura
  "mes",                      # Mes (1-12) — captura estacionalidad
  "anio"                      # Año — captura tendencias largas
]
```

#### Etiquetado (label engineering)
La clase IVT se calcula con una fórmula compuesta antes del entrenamiento:

```python
IVT = 0.40 × upra_score + 0.35 × clima_score + 0.25 × temporal_score

# Umbrales:
# BAJA  → IVT < 0.33
# MEDIA → 0.33 ≤ IVT < 0.67
# ALTA  → IVT ≥ 0.67
```

#### Métricas objetivo

| Métrica | Valor objetivo | Descripción |
|---|---|---|
| Accuracy | ≥ 0.80 | Exactitud global |
| F1 Macro | ≥ 0.78 | F1 ponderado equitativamente |
| AUC-ROC | ≥ 0.90 | Separabilidad de clases |

---

### 2. Clustering Territorial

**Archivo:** `ml/clustering.py`  
**Tipos:** KMeans + DBSCAN

#### KMeans
- Número de clusters: 4 (determinado por método del codo)
- Features: precios agrícolas + precipitación + temperatura
- Etiquetas de cluster: `C0` a `C3`

#### DBSCAN
- Usado para detectar municipios atípicos (puntos de ruido)
- `eps=0.5`, `min_samples=5`
- Etiqueta `-1` = outlier geográfico

---

### 3. Forecasting — Series Temporales

**Archivo:** `ml/forecasting.py`

#### Modelos implementados
- **Holt-Winters (ETS):** Para series con estacionalidad clara (precios UPRA)
- **SARIMA:** Para series con componente estacional e irregular (precipitación)

#### Hiperparámetros SARIMA
```python
order = (1, 1, 1)          # p, d, q
seasonal_order = (1, 1, 1, 12)  # P, D, Q, s (mensual)
```

#### Series disponibles para pronóstico
- `upra_indice_total` — Índice de precios UPRA (6 meses default)
- `precipitacion_media` — Precipitación mensual promedio nacional

---

### 4. Detección de Anomalías

**Archivo:** `ml/anomaly.py`

#### Modelos implementados
- **Isolation Forest:** Detecta puntos aislados en espacio de features multidimensional
- **Local Outlier Factor (LOF):** Detecta anomalías basado en densidad local

#### Score de anomalía
- Rango: `-1.0` a `0.0` (Isolation Forest convention)
- `score < -0.2` → Anomalía ALTA
- `-0.2 ≤ score < -0.1` → Anomalía MEDIA
- `score ≥ -0.1` → Normal

---

### 5. Explicabilidad (XAI)

**Archivo:** `ml/explainability.py`  
**Librería:** SHAP 0.45 (TreeExplainer)

#### SHAP Values
- Calculados sobre el modelo Random Forest del ensemble
- `TreeExplainer` (eficiente para modelos basados en árboles)
- Retorna importancia de cada feature para cada predicción

#### Importancia de features (típica)
```
upra_indice_total        ████████████ 0.31
upra_var_mensual_pct     ████████ 0.22
ideam_precipitacion_mm   ██████ 0.16
upra_fertilizantes       █████ 0.14
mes                      ████ 0.09
...
```

---

## Entrenamiento

### Entrenamiento básico (IVT)
```bash
# Desde la raíz del proyecto, con venv activo
python -m ml.train

# Forzar re-entrenamiento aunque el modelo exista
python -m ml.train --force
```

### Entrenamiento avanzado (todos los modelos)
```bash
# Todos los modelos de una vez
python -m ml.train_advanced

# Por modelo individual
python -m ml.train_advanced --modelo ensemble
python -m ml.train_advanced --modelo clustering
python -m ml.train_advanced --modelo forecasting
python -m ml.train_advanced --modelo anomaly
python -m ml.train_advanced --modelo xai
```

Con Make:
```bash
make train-advanced
```

### Requisito previo
Los datos deben estar cargados en la base de datos antes de entrenar:
```bash
make etl       # cargar todos los datasets
make train-advanced  # entrenar
```

---

## Validación

```bash
python -m ml.validation_report
# o
make validate
```

Genera un JSON en `data/06_validation/validation_report_YYYY-MM-DD.json` con métricas de validación cruzada 5-fold.

**Métricas calculadas:**
- Accuracy global
- F1 por clase (BAJA, MEDIA, ALTA)
- F1 Macro
- Precision Macro
- Recall Macro
- AUC-ROC (one-vs-rest)
- Validación cruzada 5-fold (F1 mean ± std)

---

## Inferencia

### Via API
```bash
# IVT con datos reales
GET /prediccion/actual

# IVT con parámetros personalizados
POST /prediccion/simular
{
  "upra_indice": 130.0,
  "upra_var_pct": 2.5,
  "precipitacion_mm": 200.0,
  "temperatura_c": 24.0
}
```

### Via Python
```python
from ml.ensemble import IVTEnsemble

modelo = IVTEnsemble()
modelo.load()  # carga desde ml/models/ivt_model.pkl

resultado = modelo.predict({
    "upra_indice_total": 124.5,
    "upra_var_mensual_pct": 0.8,
    "ideam_precipitacion_mm": 145.2,
    # ...
})
print(resultado["etiqueta"])  # "MEDIA"
```

---

## Modelos guardados

Los modelos se serializan con `joblib` en `ml/models/`:

| Archivo | Modelo | Tamaño aprox. |
|---|---|---|
| `ivt_model.pkl` | IVT Ensemble (RF + XGBoost) | ~15 MB |
| `clustering_model.pkl` | KMeans + DBSCAN | ~1 MB |
| `forecasting_upra.pkl` | Holt-Winters UPRA | ~100 KB |
| `anomaly_model.pkl` | Isolation Forest + LOF | ~5 MB |
| `shap_explainer.pkl` | TreeExplainer | ~20 MB |

> ⚠️ Los archivos `.pkl` están en `.gitignore`. No subir al repo.  
> Re-entrenar con `make train-advanced` al clonar el proyecto.

---

## Comportamiento sin modelo entrenado

Si los modelos no están entrenados, todos los endpoints ML responden:
```json
{
  "modelo_disponible": false,
  "mensaje": "Modelo no entrenado. Ejecuta: make train-advanced"
}
```

El frontend maneja esta condición mostrando un banner informativo con el comando a ejecutar.

---

## Reentrenamiento programado

Para mantener los modelos actualizados con nuevos datos:

```bash
# Con Make (combina ETL + entrenamiento)
make etl && make train-advanced && make validate
```

Recomendado: ejecutar mensualmente o cuando se actualicen los datasets.
