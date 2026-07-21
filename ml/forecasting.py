"""
ml/forecasting.py
=================
Forecasting de series temporales para Kwesx AI.

Modelos implementados
---------------------
1. Holt-Winters (Exponential Smoothing) — Captura nivel + tendencia + estacionalidad.
   Ideal para la serie UPRA (mensual, patrón estacional colombiano).

2. ARIMA — AutoRegressive Integrated Moving Average.
   Robusto para series con tendencia y autocorrelación.

3. Ensemble de forecasting — Promedio ponderado de Holt-Winters y ARIMA.
   Reduce el error al combinar los dos modelos complementarios.

Variables que se pronostican
----------------------------
- Índice UPRA de precios de insumos agrícolas (6 y 12 meses)
- Precipitación IDEAM mensual (6 meses, régimen bimodal colombiano)
- Temperatura IDEAM mensual (6 meses)

Output del forecast
-------------------
{
  "serie":           "upra_indice_total",
  "modelo":          "Holt-Winters + ARIMA ensemble",
  "n_historico":     89,
  "horizonte_meses": 6,
  "predicciones": [
    {
      "mes":       "2026-08",
      "valor":     128.4,
      "ic_inf_95": 122.1,
      "ic_sup_95": 134.7,
      "tendencia": "alcista"
    },
    ...
  ],
  "metricas": {"rmse": 2.3, "mae": 1.8, "mape": 1.5},
  "interpretacion": "Se espera un aumento del 3.2% en los precios..."
}
"""

from __future__ import annotations

import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

MODEL_DIR        = Path(__file__).parent / "models"
FORECAST_PATH    = MODEL_DIR / "forecasting.pkl"
FORECAST_META    = MODEL_DIR / "forecasting_metadata.json"

SERIES_CONFIG = {
    "upra_indice_total": {
        "nombre":       "Índice de precios de insumos agrícolas (UPRA)",
        "unidad":       "Índice base 100",
        "estacional":   12,
        "transformar":  "log",    # log-transform para estabilizar varianza
        "descripcion":  "Evolución mensual del costo de insumos agrícolas en Colombia",
    },
    "ideam_precipitacion_mm": {
        "nombre":       "Precipitación mensual promedio nacional",
        "unidad":       "mm/mes",
        "estacional":   12,
        "transformar":  "sqrt",   # sqrt para series no-negativas con varianza creciente
        "descripcion":  "Precipitación mensual histórica y proyectada",
    },
    "ideam_temperatura_c": {
        "nombre":       "Temperatura media mensual nacional",
        "unidad":       "°C",
        "estacional":   12,
        "transformar":  None,     # temperatura no necesita transformación
        "descripcion":  "Temperatura media mensual histórica y proyectada",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades de series temporales
# ─────────────────────────────────────────────────────────────────────────────

def _es_estacionaria(serie: pd.Series, alpha: float = 0.05) -> bool:
    """Test ADF para estacionariedad. Retorna True si la serie es estacionaria."""
    try:
        _, p_value, _, _, _, _ = adfuller(serie.dropna(), autolag="AIC")
        return p_value < alpha
    except Exception:
        return False


def _aplicar_transformacion(serie: pd.Series, transformar: str | None) -> pd.Series:
    if transformar == "log":
        return np.log(serie.clip(lower=0.01))
    elif transformar == "sqrt":
        return np.sqrt(serie.clip(lower=0.0))
    return serie


def _invertir_transformacion(valores: np.ndarray, transformar: str | None) -> np.ndarray:
    if transformar == "log":
        return np.exp(valores)
    elif transformar == "sqrt":
        return np.square(valores)
    return valores


def _calcular_metricas(y_real: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """RMSE, MAE, MAPE para evaluación in-sample."""
    y_real = np.array(y_real, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mask = ~np.isnan(y_real) & ~np.isnan(y_pred) & (y_real != 0)

    if mask.sum() == 0:
        return {"rmse": 0.0, "mae": 0.0, "mape": 0.0}

    residuos = y_real[mask] - y_pred[mask]
    rmse = float(np.sqrt(np.mean(residuos ** 2)))
    mae  = float(np.mean(np.abs(residuos)))
    mape = float(np.mean(np.abs(residuos / y_real[mask])) * 100)
    return {"rmse": round(rmse, 4), "mae": round(mae, 4), "mape": round(mape, 4)}


# ─────────────────────────────────────────────────────────────────────────────
# Clase principal
# ─────────────────────────────────────────────────────────────────────────────

class ForecastingTerritorial:
    """
    Motor de predicción de series temporales para Kwesx AI.

    Para cada serie ajusta Holt-Winters y SARIMA y genera un ensemble
    con intervalos de confianza al 80% y 95%.
    """

    def __init__(self):
        self.modelos_hw: dict[str, Any] = {}      # Holt-Winters por serie
        self.modelos_arima: dict[str, Any] = {}   # SARIMA por serie
        self.historicos: dict[str, pd.Series] = {}
        self.metadata: dict[str, Any] = {}

    # ── Entrenamiento ─────────────────────────────────────────────────────────

    def train(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Ajusta los modelos para todas las series configuradas.

        Parámetros
        ----------
        df : DataFrame con columna 'fecha' (datetime) y las series numéricas.

        Retorna metadatos del ajuste.
        """
        if "fecha" not in df.columns:
            raise ValueError("El DataFrame debe tener columna 'fecha'.")

        df_sorted = df.sort_values("fecha").reset_index(drop=True)
        metricas_series: dict[str, dict] = {}

        for serie_col, config in SERIES_CONFIG.items():
            if serie_col not in df_sorted.columns:
                logger.warning(f"[Forecasting] Columna '{serie_col}' no encontrada. Omitiendo.")
                continue

            serie = df_sorted.set_index("fecha")[serie_col].dropna()
            if len(serie) < 12:
                logger.warning(f"[Forecasting] '{serie_col}' tiene solo {len(serie)} puntos. Mínimo 12.")
                continue

            # Asignar frecuencia mensual
            try:
                serie.index = pd.DatetimeIndex(serie.index).to_period("M").to_timestamp()
                serie = serie.asfreq("MS")
                serie = serie.interpolate(method="linear")
            except Exception as e:
                logger.warning(f"[Forecasting] Error al preparar índice de '{serie_col}': {e}")

            self.historicos[serie_col] = serie
            transformar = config.get("transformar")

            # Transformar para estabilizar varianza
            serie_t = _aplicar_transformacion(serie, transformar)

            # Holt-Winters
            hw_fitted, hw_ok = self._ajustar_hw(serie_t, config)

            # SARIMA
            arima_fitted, arima_ok = self._ajustar_arima(serie_t, config)

            self.modelos_hw[serie_col]    = hw_fitted
            self.modelos_arima[serie_col] = arima_fitted

            # Métricas in-sample
            if hw_ok:
                y_hw = _invertir_transformacion(hw_fitted.fittedvalues.values, transformar)
                m_hw = _calcular_metricas(serie.values[:len(y_hw)], y_hw)
            else:
                m_hw = {"rmse": None, "mae": None, "mape": None}

            if arima_ok:
                y_arima = _invertir_transformacion(arima_fitted.fittedvalues.values, transformar)
                m_arima = _calcular_metricas(serie.values[:len(y_arima)], y_arima)
            else:
                m_arima = {"rmse": None, "mae": None, "mape": None}

            metricas_series[serie_col] = {
                "n_puntos":          len(serie),
                "periodo_inicio":    str(serie.index[0].date()),
                "periodo_fin":       str(serie.index[-1].date()),
                "es_estacionaria":   _es_estacionaria(serie),
                "hw_disponible":     hw_ok,
                "arima_disponible":  arima_ok,
                "metricas_hw":       m_hw,
                "metricas_arima":    m_arima,
            }
            logger.info(
                f"[Forecasting] '{serie_col}' ajustado. "
                f"HW RMSE: {m_hw.get('rmse', '?')} | ARIMA RMSE: {m_arima.get('rmse', '?')}"
            )

        self.metadata = {
            "series":       list(self.historicos.keys()),
            "metricas":     metricas_series,
            "entrenado_en": datetime.now().isoformat(),
        }

        logger.success(f"[Forecasting] {len(self.historicos)} series ajustadas.")
        return self.metadata

    def _ajustar_hw(
        self,
        serie: pd.Series,
        config: dict,
    ) -> tuple[Any, bool]:
        """Ajusta Holt-Winters con estacionalidad multiplicativa o aditiva."""
        seasonal_periods = config.get("estacional", 12)
        # Si hay menos de 2 ciclos completos, usar aditivo
        tipo_estacional = "multiplicative" if len(serie) >= 2 * seasonal_periods else "additive"
        try:
            modelo = ExponentialSmoothing(
                serie,
                trend="add",
                seasonal=tipo_estacional,
                seasonal_periods=seasonal_periods,
                damped_trend=True,
                initialization_method="estimated",
            )
            fitted = modelo.fit(optimized=True, remove_bias=True)
            return fitted, True
        except Exception as e:
            logger.warning(f"[Forecasting] HW falló: {e}. Intentando sin estacionalidad...")
            try:
                modelo = ExponentialSmoothing(serie, trend="add", damped_trend=True)
                return modelo.fit(optimized=True), True
            except Exception:
                return None, False

    def _ajustar_arima(
        self,
        serie: pd.Series,
        config: dict,
    ) -> tuple[Any, bool]:
        """Ajusta SARIMA con parámetros automáticos simplificados."""
        s = config.get("estacional", 12)
        # Órdenes estándar para datos mensuales con estacionalidad anual
        ordenes_intentar = [
            ((1, 1, 1), (1, 1, 1, s)),
            ((1, 1, 0), (1, 1, 0, s)),
            ((0, 1, 1), (0, 1, 1, s)),
            ((1, 1, 1), (0, 0, 0, 0)),  # ARIMA simple sin parte estacional
        ]

        for orden, orden_est in ordenes_intentar:
            try:
                modelo = SARIMAX(
                    serie,
                    order=orden,
                    seasonal_order=orden_est,
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                )
                fitted = modelo.fit(
                    disp=False,
                    maxiter=100,
                    method="lbfgs",
                )
                return fitted, True
            except Exception:
                continue

        return None, False

    # ── Predicción ─────────────────────────────────────────────────────────────

    def forecast(
        self,
        serie_col: str,
        horizonte: int = 6,
        alpha_ic: float = 0.05,
    ) -> dict[str, Any]:
        """
        Genera predicciones para una serie dada.

        Parámetros
        ----------
        serie_col    : Nombre de la columna (ej: 'upra_indice_total')
        horizonte    : Número de meses a pronosticar
        alpha_ic     : Nivel de significancia para IC (0.05 = 95%)

        Retorna
        -------
        dict con predicciones, intervalos de confianza e interpretación
        """
        if serie_col not in self.historicos:
            return {"error": f"Serie '{serie_col}' no disponible. Entrena primero."}

        config     = SERIES_CONFIG.get(serie_col, {})
        transformar = config.get("transformar")
        serie_hist = self.historicos[serie_col]
        serie_t    = _aplicar_transformacion(serie_hist, transformar)

        # Fechas futuras
        ultimo_periodo = serie_hist.index[-1]
        fechas_futuras = pd.date_range(
            start=ultimo_periodo + pd.DateOffset(months=1),
            periods=horizonte,
            freq="MS",
        )

        # Predicciones de Holt-Winters
        pred_hw, ic_hw_inf, ic_hw_sup = self._pred_hw(serie_col, horizonte, transformar, alpha_ic)

        # Predicciones ARIMA
        pred_arima, ic_arima_inf, ic_arima_sup = self._pred_arima(serie_col, horizonte, transformar, alpha_ic)

        # Ensemble: promedio ponderado (60% HW, 40% ARIMA si disponible)
        hw_ok    = pred_hw is not None
        arima_ok = pred_arima is not None

        if hw_ok and arima_ok:
            pred_final  = 0.6 * pred_hw + 0.4 * pred_arima
            ic_inf_final = 0.6 * ic_hw_inf + 0.4 * ic_arima_inf
            ic_sup_final = 0.6 * ic_hw_sup + 0.4 * ic_arima_sup
            modelo_usado = "Ensemble (HW 60% + SARIMA 40%)"
        elif hw_ok:
            pred_final, ic_inf_final, ic_sup_final = pred_hw, ic_hw_inf, ic_hw_sup
            modelo_usado = "Holt-Winters"
        elif arima_ok:
            pred_final, ic_inf_final, ic_sup_final = pred_arima, ic_arima_inf, ic_arima_sup
            modelo_usado = "SARIMA"
        else:
            # Fallback: tendencia lineal simple
            pred_final = self._tendencia_lineal(serie_t, horizonte, transformar)
            ic_inf_final = pred_final * 0.95
            ic_sup_final = pred_final * 1.05
            modelo_usado = "Tendencia lineal (fallback)"

        # Construir output
        ultimo_real = float(serie_hist.iloc[-1])
        primer_pred = float(pred_final[0])
        cambio_pct = (primer_pred - ultimo_real) / ultimo_real * 100

        predicciones = []
        for i, fecha in enumerate(fechas_futuras):
            v = float(pred_final[i])
            predicciones.append({
                "mes":       fecha.strftime("%Y-%m"),
                "valor":     round(v, 3),
                "ic_inf_95": round(float(ic_inf_final[i]), 3),
                "ic_sup_95": round(float(ic_sup_final[i]), 3),
                "tendencia": "alcista" if v > ultimo_real else "bajista",
            })

        # Último histórico para contexto
        historico_reciente = [
            {"mes": str(ts.to_period("M")), "valor": round(float(v), 3)}
            for ts, v in serie_hist.tail(12).items()
        ]

        return {
            "serie":              serie_col,
            "nombre":             config.get("nombre", serie_col),
            "unidad":             config.get("unidad", ""),
            "modelo":             modelo_usado,
            "n_historico":        len(serie_hist),
            "horizonte_meses":    horizonte,
            "ultimo_valor_real":  round(ultimo_real, 3),
            "cambio_esperado_pct":round(cambio_pct, 2),
            "predicciones":       predicciones,
            "historico_reciente": historico_reciente,
            "metricas":           self.metadata.get("metricas", {}).get(serie_col, {}),
            "interpretacion":     self._interpretar_forecast(
                config.get("nombre", serie_col), cambio_pct, horizonte, config.get("unidad", "")
            ),
        }

    def _pred_hw(
        self,
        serie_col: str,
        horizonte: int,
        transformar: str | None,
        alpha_ic: float,
    ) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None]:
        """Genera predicción e IC de Holt-Winters."""
        modelo = self.modelos_hw.get(serie_col)
        if modelo is None:
            return None, None, None
        try:
            sim = modelo.simulate(nsimulations=horizonte, repetitions=500)
            pred = modelo.forecast(horizonte)
            pred_inv = _invertir_transformacion(pred.values, transformar)

            sim_inv = _invertir_transformacion(sim.values, transformar)
            ic_inf = np.percentile(sim_inv, (alpha_ic / 2) * 100, axis=1)
            ic_sup = np.percentile(sim_inv, (1 - alpha_ic / 2) * 100, axis=1)
            return pred_inv, ic_inf, ic_sup
        except Exception:
            try:
                pred = modelo.forecast(horizonte)
                pred_inv = _invertir_transformacion(pred.values, transformar)
                ic_inf = pred_inv * 0.95
                ic_sup = pred_inv * 1.05
                return pred_inv, ic_inf, ic_sup
            except Exception:
                return None, None, None

    def _pred_arima(
        self,
        serie_col: str,
        horizonte: int,
        transformar: str | None,
        alpha_ic: float,
    ) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None]:
        """Genera predicción e IC de SARIMA."""
        modelo = self.modelos_arima.get(serie_col)
        if modelo is None:
            return None, None, None
        try:
            forecast_res = modelo.get_forecast(steps=horizonte)
            pred = forecast_res.predicted_mean.values
            ic   = forecast_res.conf_int(alpha=alpha_ic)

            pred_inv   = _invertir_transformacion(pred, transformar)
            ic_inf_inv = _invertir_transformacion(ic.iloc[:, 0].values, transformar)
            ic_sup_inv = _invertir_transformacion(ic.iloc[:, 1].values, transformar)
            return pred_inv, ic_inf_inv, ic_sup_inv
        except Exception:
            return None, None, None

    def _tendencia_lineal(
        self,
        serie: pd.Series,
        horizonte: int,
        transformar: str | None,
    ) -> np.ndarray:
        """Extrapolación lineal simple como fallback."""
        x = np.arange(len(serie))
        y = serie.values
        slope = np.polyfit(x, y, 1)[0]
        futuro_t = np.array([y[-1] + slope * (i + 1) for i in range(horizonte)])
        return _invertir_transformacion(futuro_t, transformar)

    def _interpretar_forecast(
        self,
        nombre: str,
        cambio_pct: float,
        horizonte: int,
        unidad: str,
    ) -> str:
        """Genera una interpretación en lenguaje natural del forecast."""
        dir_ = "aumentar" if cambio_pct > 0 else "disminuir"
        magnitud = abs(cambio_pct)

        if magnitud < 1:
            intensidad = "levemente"
        elif magnitud < 5:
            intensidad = "moderadamente"
        elif magnitud < 15:
            intensidad = "significativamente"
        else:
            intensidad = "de forma pronunciada"

        return (
            f"Se proyecta que {nombre} podría {dir_} {intensidad} "
            f"({cambio_pct:+.1f}%) en los próximos {horizonte} meses. "
            f"Este pronóstico se basa en los patrones históricos y la "
            f"estacionalidad colombiana. Monitoree regularmente para validar."
        )

    # ── Persistencia ──────────────────────────────────────────────────────────

    def save(self) -> str:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "modelos_hw":    self.modelos_hw,
            "modelos_arima": self.modelos_arima,
            "historicos":    self.historicos,
            "metadata":      self.metadata,
        }, FORECAST_PATH)
        with open(FORECAST_META, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        logger.success(f"[Forecasting] Guardado en {FORECAST_PATH}")
        return str(FORECAST_PATH)

    def load(self) -> "ForecastingTerritorial":
        if not FORECAST_PATH.exists():
            raise FileNotFoundError(f"Forecasting no encontrado en {FORECAST_PATH}.")
        data = joblib.load(FORECAST_PATH)
        self.modelos_hw    = data.get("modelos_hw", {})
        self.modelos_arima = data.get("modelos_arima", {})
        self.historicos    = data.get("historicos", {})
        self.metadata      = data.get("metadata", {})
        logger.info(f"[Forecasting] Cargado desde {FORECAST_PATH}")
        return self

    def is_trained(self) -> bool:
        return FORECAST_PATH.exists()

    # ── Lista de series disponibles ────────────────────────────────────────────

    def series_disponibles(self) -> list[dict[str, str]]:
        return [
            {"id": k, "nombre": v["nombre"], "unidad": v["unidad"]}
            for k, v in SERIES_CONFIG.items()
            if k in self.historicos
        ]
