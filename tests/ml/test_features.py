"""
Kwesx AI — Tests del Feature Engineering (ml/features.py)
"""

import pytest
import pandas as pd
import numpy as np


@pytest.mark.ml
class TestIdeamSintetico:
    """Pruebas para el fallback sintético de IDEAM."""

    def test_sintetico_returns_12_months(self):
        """El IDEAM sintético debe retornar 12 meses de datos."""
        from ml.features import _ideam_sintetico

        df = _ideam_sintetico(año=2024)
        assert len(df) == 12

    def test_sintetico_has_required_columns(self):
        """El IDEAM sintético debe tener columnas de precipitación y temperatura."""
        from ml.features import _ideam_sintetico

        df = _ideam_sintetico(año=2024)
        assert "precipitacion" in df.columns or "prec_mensual" in df.columns
        assert "temperatura" in df.columns or "temp_media" in df.columns

    def test_sintetico_precipitation_range(self):
        """La precipitación sintética debe estar en rango plausible (mm/mes)."""
        from ml.features import _ideam_sintetico

        df = _ideam_sintetico(año=2024)
        col = "precipitacion" if "precipitacion" in df.columns else "prec_mensual"
        assert df[col].min() >= 0.0
        assert df[col].max() <= 500.0, "Precipitación mensual demasiado alta"

    def test_patron_mensual_follows_colombia_normals(self):
        """El patrón debe reflejar el régimen bimodal colombiano (picos en abr-may y sep-nov)."""
        from ml.features import PATRON_PREC_MENSUAL

        # Patrón IDEAM 1961-2020: picos en meses 4-5 (abr-may) y 9-11 (sep-nov)
        assert len(PATRON_PREC_MENSUAL) == 12
        # Meses húmedos deben tener factores > 1.0
        assert PATRON_PREC_MENSUAL[3] > 1.0  # Abril (índice 3)
        assert PATRON_PREC_MENSUAL[4] > 1.0  # Mayo (índice 4)
        assert PATRON_PREC_MENSUAL[9] > 1.0  # Octubre (índice 9)


@pytest.mark.ml
class TestFeatureEngineering:
    """Pruebas para la construcción de features del modelo."""

    def test_features_no_nan(self, sample_upra_df):
        """Las features no deben contener NaN."""
        from ml.features import construir_features

        features = construir_features(sample_upra_df)
        assert not features.isnull().any().any(), (
            f"Features con NaN:\n{features.isnull().sum()}"
        )

    def test_features_has_required_columns(self, sample_upra_df):
        """Las features deben incluir columnas esenciales."""
        from ml.features import construir_features

        features = construir_features(sample_upra_df)
        required = ["upra_indice", "upra_variacion_anual", "mes", "año"]
        missing = [col for col in required if col not in features.columns]
        assert not missing, f"Columnas faltantes: {missing}"
