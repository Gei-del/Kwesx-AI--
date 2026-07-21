# Kwesx AI — Documentación de la API

**Base URL:** `http://localhost:8000` (desarrollo) · `https://kwesx-api.onrender.com` (producción)  
**Documentación interactiva:** `/docs` (Swagger UI) · `/redoc` (ReDoc)  
**Versión:** 1.0.0

---

## Autenticación

En la versión actual (Modo Demostración), todos los endpoints son públicos.  
La arquitectura de autenticación JWT está preparada para activarse en la versión de producción.

---

## Endpoints

### Sistema / Salud

#### `GET /`
Estado general de la API.

**Response 200:**
```json
{
  "proyecto": "Kwesx AI",
  "version": "1.0.0",
  "estado": "activo",
  "ambiente": "development",
  "endpoints": {
    "datos": "/datos",
    "asistente": "/asistente",
    "prediccion": "/prediccion",
    "ml": "/ml",
    "recomendaciones": "/recomendaciones",
    "salud": "/salud"
  }
}
```

#### `GET /salud`
Estado del sistema.

#### `GET /salud/etl`
Estado de todas las tablas del MTU.

**Response 200:**
```json
{
  "status": "ok",
  "mtu": {
    "ani": { "registros": 151453, "ok": true },
    "upra": { "registros": 89, "ok": true },
    "ideam": { "registros": 4200, "ok": true },
    "conectividad": { "registros": 1122, "ok": true },
    "educacion": { "registros": 3288, "ok": true }
  },
  "timestamp": "2026-07-14T10:00:00Z"
}
```

---

### Datos MTU

#### `GET /datos/resumen`
Resumen de todos los datasets cargados.

**Response 200:**
```json
{
  "ani": { "registros": 151453, "ultima_actualizacion": "2026-07-01" },
  "upra": { "registros": 89, "ultima_actualizacion": "2026-06-30" },
  "ideam": { "registros": 4200, "ultima_actualizacion": "2026-07-14" },
  "conectividad": { "registros": 1122 },
  "educacion": { "registros": 3288 }
}
```

#### `GET /datos/upra`
Serie de precios de insumos agrícolas UPRA.

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `desde` | string (ISO date) | 2 años atrás | Fecha de inicio |
| `hasta` | string (ISO date) | hoy | Fecha de fin |
| `limit` | integer | 200 | Máximo de registros |

**Response 200:**
```json
{
  "total": 89,
  "datos": [
    {
      "id": 1,
      "fecha": "2026-06-01",
      "indice_total": 124.5,
      "var_mensual_pct": 0.8,
      "fertilizantes": 128.2,
      "plaguicidas": 119.1,
      "semillas": 115.4,
      "combustible": 131.7,
      "fuente": "UPRA"
    }
  ]
}
```

**Errores:**
- `404` — No hay datos disponibles
- `500` — Error interno (ver `/salud`)

#### `GET /datos/upra/tendencia`
Tendencia histórica completa (útil para gráficas).

#### `GET /datos/ani`
Registros de tráfico vehicular en peajes ANI.

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `limit` | integer | 500 | Máximo de registros |
| `desde` | string | — | Fecha inicio |
| `departamento` | string | — | Filtrar por departamento |

**Response 200:**
```json
{
  "total": 151453,
  "datos": [
    {
      "id": 1,
      "peaje": "Chusacá",
      "departamento": "Cundinamarca",
      "municipio": "Soacha",
      "latitud": 4.5709,
      "longitud": -74.2171,
      "categoria_tarifa": "I",
      "cantidad_trafico": 8420,
      "valor_tarifa": 5900,
      "cantidad_evasores": 12,
      "fuente": "ANI"
    }
  ]
}
```

#### `GET /datos/ideam`
Variables climáticas de estaciones hidrometeorológicas.

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `limit` | integer | 1000 | Máximo de registros |
| `dias` | integer | 30 | Días hacia atrás |
| `tipo` | string | — | `precipitacion` o `temperatura` |
| `departamento` | string | — | Filtrar por departamento |

#### `GET /datos/conectividad`
Cobertura de internet por municipio (DANE + MinTIC).

| Parámetro | Tipo | Descripción |
|---|---|---|
| `departamento` | string | Filtrar por departamento |
| `anio` | integer | Año del dato |

#### `GET /datos/educacion`
Tasas de cobertura educativa por municipio (MEN-SIMAT).

| Parámetro | Tipo | Descripción |
|---|---|---|
| `departamento` | string | Filtrar por departamento |
| `nivel` | string | `preescolar`, `primaria`, `secundaria`, `media` |

---

### Asistente IA

#### `POST /asistente/chat`
Consulta en lenguaje natural sobre el territorio colombiano.

**Request body:**
```json
{
  "texto": "¿Cómo están los precios de los fertilizantes este mes?",
  "contexto": {}
}
```

**Response 200:**
```json
{
  "intencion": "precios",
  "respuesta": "Los precios de los insumos agrícolas muestran una variación de +0.8% mensual...",
  "datos": {
    "indice_total": 124.5,
    "var_mensual_pct": 0.8
  },
  "sugerencias": [
    "¿Qué fertilizantes subieron más?",
    "¿Cómo están los precios vs el año pasado?",
    "¿Qué zona tiene mayor riesgo agrícola?"
  ],
  "confianza": 0.87
}
```

**Intenciones reconocidas:** `precios`, `clima`, `vias`, `conectividad`, `educacion`, `riesgos`, `ivt`, `saludo`

#### `GET /asistente/ejemplos`
Lista de preguntas de ejemplo para el asistente.

---

### Predicción IVT

#### `GET /prediccion/actual`
Índice de Vulnerabilidad Territorial actual basado en datos recientes.

**Response 200 (modelo disponible):**
```json
{
  "modelo_disponible": true,
  "ivt": {
    "clase": 1,
    "etiqueta": "MEDIA",
    "probabilidades": { "BAJA": 0.22, "MEDIA": 0.61, "ALTA": 0.17 },
    "confianza": 0.61
  },
  "inputs": {
    "upra_indice_total": 124.5,
    "upra_variacion_pct": 0.8,
    "precipitacion_mm": 145.2,
    "temperatura_c": 22.1
  },
  "interpretacion": "Vulnerabilidad moderada. Los precios agrícolas muestran estabilidad pero la precipitación está por encima del promedio histórico.",
  "fecha_calculo": "2026-07-14T10:00:00Z"
}
```

**Response 200 (modelo no entrenado):**
```json
{
  "modelo_disponible": false,
  "mensaje": "Modelo no entrenado. Ejecuta: python -m ml.train"
}
```

#### `POST /prediccion/simular`
Simula el IVT con parámetros personalizados.

**Request body:**
```json
{
  "upra_indice": 130.0,
  "upra_var_pct": 2.5,
  "upra_fertilizantes": 135.0,
  "upra_plaguicidas": 125.0,
  "precipitacion_mm": 250.0,
  "temperatura_c": 25.0
}
```

---

### Machine Learning Avanzado

#### `GET /ml/estado`
Estado de todos los modelos ML (entrenados o no).

#### `GET /ml/insights`
Insights completos: ensemble, clustering, forecasting, anomalías, XAI.

#### `GET /ml/forecast/{serie}`
Pronóstico de serie temporal.

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `serie` | string (path) | `upra_indice_total` | Serie a predecir |
| `horizonte` | integer (query) | 6 | Meses hacia adelante |

#### `GET /ml/anomalias`
Anomalías detectadas por Isolation Forest + LOF.

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `top` | integer | 8 | Máximo de anomalías a retornar |

#### `GET /ml/clustering`
Segmentación territorial por KMeans + DBSCAN.

#### `GET /ml/explicacion`
Explicación SHAP del modelo IVT.

#### `GET /ml/validacion`
Métricas de validación cruzada del ensemble.

**Response 200:**
```json
{
  "modelo_disponible": true,
  "metricas": {
    "accuracy": 0.847,
    "f1_macro": 0.831,
    "precision_macro": 0.839,
    "recall_macro": 0.825,
    "auc_roc": 0.912
  },
  "cross_validation": {
    "folds": 5,
    "f1_scores": [0.82, 0.85, 0.83, 0.84, 0.81],
    "f1_mean": 0.831,
    "f1_std": 0.014
  }
}
```

---

### Recomendaciones IA

#### `GET /recomendaciones`
Recomendaciones territoriales priorizadas por IA.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `municipio` | string | Filtrar por municipio |
| `departamento` | string | Filtrar por departamento |

**Response 200:**
```json
{
  "recomendaciones": [
    {
      "tipo": "alerta_climatica",
      "titulo": "Precipitación por encima del promedio",
      "descripcion": "Las lluvias en los últimos 30 días superan el promedio en un 23%...",
      "acciones": [
        "Reforzar drenajes en cultivos",
        "Revisar infraestructura vial antes de transportar cosecha"
      ],
      "prioridad": "ALTA",
      "datos_base": { "precipitacion_mm": 187.4, "anomalia_pct": 23 }
    }
  ]
}
```

---

## Códigos de error

| Código | Significado |
|---|---|
| `400` | Parámetros inválidos |
| `404` | Recurso no encontrado |
| `429` | Rate limit excedido (30 req/min en asistente, 120/min en datos) |
| `500` | Error interno del servidor |

---

## Rate Limiting

| Endpoint | Límite |
|---|---|
| `/asistente/chat` | 30 req/min |
| `/datos/*` | 120 req/min |
| `/ml/*` | 20 req/min |
| Resto | 200 req/min |

---

## Ejemplo de uso con curl

```bash
# Estado de la API
curl http://localhost:8000/

# Consultar precios UPRA
curl "http://localhost:8000/datos/upra?limit=5"

# Consultar el asistente
curl -X POST http://localhost:8000/asistente/chat \
  -H "Content-Type: application/json" \
  -d '{"texto": "¿cómo está el clima en Colombia?"}'

# IVT actual
curl http://localhost:8000/prediccion/actual

# Recomendaciones
curl "http://localhost:8000/recomendaciones?departamento=Cundinamarca"
```
