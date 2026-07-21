"""
ml/features.py
==============
Ingenieria de caracteristicas para el modelo de IA territorial de Kwesx AI.

Cruza 3 fuentes del MTU:
  - UPRA  -> presion de costos agricolas (variacion del indice mensual)
  - IDEAM -> anomalias climaticas (desviacion respecto a la normal historica)
  - ANI   -> intensidad de trafico (proxy de actividad economica)

Notas de implementacion
-----------------------
- pd.to_period() como funcion del modulo fue eliminado en pandas >= 2.0.
  Se usa siempre la forma correcta: Series.dt.to_period("M")
- Si la API de IDEAM falla o devuelve pocos datos, se usa un generador
  de datos sinteticos basado en las Normales Climatologicas del IDEAM
  (periodo 1961-2020). Esto garantiza que el entrenamiento siempre funcione.
"""

import pandas as pd
import numpy as np
import requests
from loguru import logger
from datetime import date, timedelta

from etl.config import (
    SOCRATA_BASE,
    SOCRATA_HEADERS,
    UPRA_DATASET_ID,
    IDEAM_PRECIPITACION_ID,
    IDEAM_TEMPERATURA_ID,
)

# ─────────────────────────────────────────────────────────────────────────────
# Normales climaticas historicas (IDEAM 1961-2020, promedio nacional)
# Fuente: dataset nsz2-kzcq en datos.gov.co
# ─────────────────────────────────────────────────────────────────────────────
NORMAL_PRECIPITACION_MM = 150.0   # mm/mes promedio anual nacional
NORMAL_TEMPERATURA_C    = 22.0    # grados C promedio anual nacional

# Patron mensual: cuanto varia cada mes respecto al promedio anual (%)
# Meses 1-12. Colombia tiene 2 temporadas de lluvias (abr-may, oct-nov).
PATRON_PREC_MENSUAL = [0.53, 0.73, 0.97, 1.27, 1.33, 0.87, 0.67, 0.77, 1.13, 1.33, 1.10, 0.70]
PATRON_TEMP_MENSUAL = [1.00, 1.02, 1.04, 1.04, 1.02, 1.00, 0.98, 0.98, 1.00, 1.00, 0.98, 0.98]

# Columnas del modelo (mismo orden en que se entrena)
FEATURE_COLS = [
    "upra_indice_total",
    "upra_var_mensual_pct",
    "upra_fertilizantes",
    "upra_plaguicidas",
    "ideam_precipitacion_mm",
    "ideam_precipitacion_anomalia",
    "ideam_temperatura_c",
    "ideam_temperatura_anomalia",
    "mes",
    "anio",
]


# ─────────────────────────────────────────────────────────────────────────────
# Builder principal
# ─────────────────────────────────────────────────────────────────────────────

def build_feature_matrix_from_api() -> pd.DataFrame:
    """
    Construye la matriz de features desde la API Socrata.

    Returns
    -------
    pd.DataFrame con FEATURE_COLS + columna 'fecha' (una fila por mes UPRA).
    """
    logger.info("[Features] Construyendo features desde API Socrata...")

    # 1. UPRA (fuente principal, 89 filas, muy confiable)
    upra_df = _fetch_upra()
    if upra_df.empty:
        raise RuntimeError("No se pudieron obtener datos UPRA de la API.")

    # 2. IDEAM — intentamos obtener datos reales; si falla, usamos sinteticos
    prec_df = _fetch_ideam_mensual(IDEAM_PRECIPITACION_ID, "precipitacion_mm")
    temp_df = _fetch_ideam_mensual(IDEAM_TEMPERATURA_ID, "temperatura_c")

    # 3. Merge y calculo de anomalias
    df = _merge_features(upra_df, prec_df, temp_df)

    logger.success(
        f"[Features] Matriz lista: {df.shape[0]} filas x {df.shape[1]} columnas "
        f"| Periodo: {df['fecha'].min().date()} -> {df['fecha'].max().date()}"
    )
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Fetchers individuales
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_upra() -> pd.DataFrame:
    """Descarga y prepara la serie mensual UPRA."""
    url = f"{SOCRATA_BASE}/{UPRA_DATASET_ID}.json"
    params = {
        "$select": "fecha, indice_total, total_fertilizantes, total_plaguicidas",
        "$order": "fecha",
        "$limit": 200,
    }
    try:
        resp = requests.get(url, headers=SOCRATA_HEADERS, params=params, timeout=60)
        resp.raise_for_status()
        rows = resp.json()
    except Exception as e:
        logger.error(f"[Features/UPRA] Error: {e}")
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["fecha"] = pd.to_datetime(df["fecha"])

    for col in ["indice_total", "total_fertilizantes", "total_plaguicidas"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values("fecha").reset_index(drop=True)

    # Variacion mensual del indice total (% vs mes anterior)
    df["upra_var_mensual_pct"] = (df["indice_total"].pct_change() * 100).round(3)

    # Period de ano-mes para join con IDEAM
    df["anio_mes"] = df["fecha"].dt.to_period("M")   # CORRECTO: .dt.to_period en Series

    df = df.rename(columns={
        "indice_total":        "upra_indice_total",
        "total_fertilizantes": "upra_fertilizantes",
        "total_plaguicidas":   "upra_plaguicidas",
    })

    logger.info(f"[Features/UPRA] {len(df)} meses disponibles.")
    return df[["fecha", "anio_mes", "upra_indice_total", "upra_var_mensual_pct",
               "upra_fertilizantes", "upra_plaguicidas"]]


def _fetch_ideam_mensual(dataset_id: str, col_name: str) -> pd.DataFrame:
    """
    Descarga datos IDEAM y los agrega a promedios mensuales nacionales.

    Estrategia de 3 niveles:
      1. Fetch de 5,000 registros recientes + agrupacion client-side (rapido)
      2. Si falla o hay menos de 3 meses: datos sinteticos estacionales
    """
    url = f"{SOCRATA_BASE}/{dataset_id}.json"
    params = {
        "$select": "fechaobservacion, valorobservado",
        "$order":  "fechaobservacion DESC",
        "$limit":  5000,
    }
    try:
        resp = requests.get(url, headers=SOCRATA_HEADERS, params=params, timeout=45)
        resp.raise_for_status()
        rows = resp.json()
    except Exception as e:
        logger.warning(
            f"[Features/IDEAM {col_name}] Timeout/error ({e}). "
            "Usando datos sinteticos basados en normales IDEAM 1961-2020."
        )
        return _ideam_sintetico(col_name)

    if not rows:
        logger.warning(f"[Features/IDEAM {col_name}] API devolvio 0 filas. Usando datos sinteticos.")
        return _ideam_sintetico(col_name)

    df = pd.DataFrame(rows)
    df["fechaobservacion"] = pd.to_datetime(df["fechaobservacion"], errors="coerce")
    df["valorobservado"]   = pd.to_numeric(df["valorobservado"], errors="coerce")

    # Eliminar NaN y valores fisicamente imposibles
    if col_name == "precipitacion_mm":
        df = df[(df["valorobservado"] >= 0) & (df["valorobservado"] < 1000)]
    elif col_name == "temperatura_c":
        df = df[(df["valorobservado"] > -5) & (df["valorobservado"] < 45)]

    df = df.dropna(subset=["fechaobservacion", "valorobservado"])

    if df.empty:
        return _ideam_sintetico(col_name)

    # Agrupar por mes usando dt.to_period en la Serie (pandas 2.x correcto)
    df["anio_mes"] = df["fechaobservacion"].dt.to_period("M")
    resultado = (
        df.groupby("anio_mes")["valorobservado"]
        .mean()
        .reset_index()
        .rename(columns={"valorobservado": col_name})
    )

    meses_reales = len(resultado)
    logger.info(f"[Features/IDEAM {col_name}] {meses_reales} meses de datos reales.")

    if meses_reales < 3:
        logger.warning(
            f"[Features/IDEAM {col_name}] Solo {meses_reales} mes(es) — "
            "complementando con normales IDEAM para el rango completo."
        )
        return _ideam_sintetico(col_name)

    return resultado[["anio_mes", col_name]]


def _ideam_sintetico(col_name: str) -> pd.DataFrame:
    """
    Genera una serie mensual sintetica basada en las Normales Climatologicas
    del IDEAM (periodo 1961-2020, cobertura nacional).

    Cubre el mismo rango de fechas que UPRA (ene 2021 - presente) con
    patrones estacionales realistas de Colombia:
      - Temporadas de lluvia: abril-mayo y octubre-noviembre
      - Temporada seca: diciembre-enero y junio-agosto

    Esto garantiza que el modelo capte estacionalidad real aunque la API
    de IDEAM no este disponible durante el entrenamiento.
    """
    logger.info(f"[Features/IDEAM {col_name}] Generando serie sintetica (normales IDEAM)...")

    fechas = pd.date_range(start="2021-01-01", end=date.today().strftime("%Y-%m-01"), freq="MS")
    valores = []

    for f in fechas:
        mes = f.month  # 1-12
        if col_name == "precipitacion_mm":
            base = NORMAL_PRECIPITACION_MM * PATRON_PREC_MENSUAL[mes - 1]
            # Variacion interanual pequena (+-10%) para que no sean todos identicos
            ruido = np.random.normal(0, base * 0.08)
            valores.append(max(0.0, round(base + ruido, 1)))
        else:  # temperatura_c
            base = NORMAL_TEMPERATURA_C * PATRON_TEMP_MENSUAL[mes - 1]
            ruido = np.random.normal(0, 0.3)
            valores.append(round(base + ruido, 2))

    df = pd.DataFrame({
        "anio_mes":  fechas.to_period("M"),   # Period("2021-01", "M")
        col_name:    valores,
    })

    logger.info(
        f"[Features/IDEAM {col_name}] Serie sintetica generada: "
        f"{len(df)} meses (normales IDEAM 1961-2020 con estacionalidad)."
    )
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Merge y calculo de anomalias
# ─────────────────────────────────────────────────────────────────────────────

def _merge_features(
    upra_df: pd.DataFrame,
    prec_df: pd.DataFrame,
    temp_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Une las 3 fuentes por anio_mes y calcula anomalias climaticas.
    """
    df = upra_df.merge(prec_df, on="anio_mes", how="left")
    df = df.merge(temp_df,  on="anio_mes", how="left")

    # Interpolacion lineal para meses sin datos IDEAM
    for col in ["precipitacion_mm", "temperatura_c"]:
        if col in df.columns:
            df[col] = df[col].interpolate(method="linear", limit_direction="both")

    # Fallback a la normal si aun hay NaN
    df["precipitacion_mm"] = df.get("precipitacion_mm", pd.Series(NORMAL_PRECIPITACION_MM)).fillna(NORMAL_PRECIPITACION_MM)
    df["temperatura_c"]    = df.get("temperatura_c",    pd.Series(NORMAL_TEMPERATURA_C)).fillna(NORMAL_TEMPERATURA_C)

    # Anomalias climaticas (desviacion vs normal historica)
    df["ideam_precipitacion_mm"]       = df["precipitacion_mm"]
    df["ideam_precipitacion_anomalia"] = (df["precipitacion_mm"] - NORMAL_PRECIPITACION_MM).round(2)
    df["ideam_temperatura_c"]          = df["temperatura_c"]
    df["ideam_temperatura_anomalia"]   = (df["temperatura_c"] - NORMAL_TEMPERATURA_C).round(3)

    # Features temporales (captura estacionalidad y tendencia)
    df["mes"]  = df["fecha"].dt.month
    df["anio"] = df["fecha"].dt.year

    # Primer mes no tiene variacion mensual
    df["upra_var_mensual_pct"] = df["upra_var_mensual_pct"].fillna(0.0)

    return df.dropna(subset=["upra_indice_total"])


# ─────────────────────────────────────────────────────────────────────────────
# Builder para prediccion puntual (usado por predict.py y el endpoint)
# ─────────────────────────────────────────────────────────────────────────────

def build_prediction_features(
    upra_indice: float,
    upra_var_pct: float,
    upra_fertilizantes: float,
    upra_plaguicidas: float,
    precipitacion_mm: float,
    temperatura_c: float,
    fecha: date,
) -> pd.DataFrame:
    """
    Construye un DataFrame de 1 fila para una prediccion puntual.
    Retorna exactamente las columnas de FEATURE_COLS.
    """
    row = {
        "upra_indice_total":            upra_indice,
        "upra_var_mensual_pct":         upra_var_pct,
        "upra_fertilizantes":           upra_fertilizantes,
        "upra_plaguicidas":             upra_plaguicidas,
        "ideam_precipitacion_mm":       precipitacion_mm,
        "ideam_precipitacion_anomalia": round(precipitacion_mm - NORMAL_PRECIPITACION_MM, 2),
        "ideam_temperatura_c":          temperatura_c,
        "ideam_temperatura_anomalia":   round(temperatura_c - NORMAL_TEMPERATURA_C, 3),
        "mes":                          fecha.month,
        "anio":                         fecha.year,
    }
    return pd.DataFrame([row])[FEATURE_COLS]
