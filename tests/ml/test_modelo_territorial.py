"""
Kwesx AI — Tests del Modelo IVT (Índice de Vulnerabilidad Territorial)
"""

import pytest
import numpy as np
import pandas as pd


# ── Tests de la función compute_ivt_score ─────────────────────────────────────

@pytest.mark.ml
class TestComputeIvtScore:
    """Pruebas unitarias para compute_ivt_score."""

    def test_score_range_is_0_to_100(self):
        """El score IVT siempre debe estar en el rango [0, 100]."""
        from ml.modelo_territorial import compute_ivt_score

        test_cases = [
            {"indice": 100.0, "variacion_mensual": 0.0, "variacion_anual": 0.0,
             "precipitacion": 50.0, "temperatura": 22.0, "mes": 6, "año": 2024},
            {"indice": 130.0, "variacion_mensual": 5.0, "variacion_anual": 30.0,
             "precipitacion": 200.0, "temperatura": 28.0, "mes": 10, "año": 2023},
            {"indice": 90.0, "variacion_mensual": -3.0, "variacion_anual": -5.0,
             "precipitacion": 10.0, "temperatura": 15.0, "mes": 1, "año": 2020},
        ]

        for case in test_cases:
            score = compute_ivt_score(**case)
            assert 0.0 <= score <= 100.0, f"Score fuera de rango: {score} para {case}"

    def test_alta_inflacion_2022_2023_increases_score(self):
        """Años de alta inflación (2022-2023) deben producir scores más altos."""
        from ml.modelo_territorial import compute_ivt_score

        base_params = {
            "indice": 115.0, "variacion_mensual": 2.0, "variacion_anual": 8.0,
            "precipitacion": 80.0, "temperatura": 22.0, "mes": 6
        }

        score_2022 = compute_ivt_score(**base_params, año=2022)
        score_2020 = compute_ivt_score(**base_params, año=2020)

        assert score_2022 > score_2020, (
            f"Score 2022 ({score_2022}) debe ser mayor que 2020 ({score_2020})"
        )

    def test_harvest_months_sep_nov_increase_score(self):
        """Meses de cosecha (sep-nov) deben producir scores más altos."""
        from ml.modelo_territorial import compute_ivt_score

        base_params = {
            "indice": 112.0, "variacion_mensual": 1.5, "variacion_anual": 6.0,
            "precipitacion": 90.0, "temperatura": 22.0, "año": 2024
        }

        score_oct = compute_ivt_score(**base_params, mes=10)   # cosecha
        score_feb = compute_ivt_score(**base_params, mes=2)    # no cosecha

        assert score_oct > score_feb, (
            f"Score octubre ({score_oct}) debe ser mayor que febrero ({score_feb})"
        )

    def test_high_variacion_anual_increases_score(self):
        """Mayor variación anual del precio debe aumentar el score."""
        from ml.modelo_territorial import compute_ivt_score

        base_params = {
            "indice": 112.0, "variacion_mensual": 1.0,
            "precipitacion": 80.0, "temperatura": 22.0, "mes": 6, "año": 2024
        }

        score_low = compute_ivt_score(**base_params, variacion_anual=2.0)
        score_high = compute_ivt_score(**base_params, variacion_anual=15.0)

        assert score_high > score_low

    def test_score_is_float(self):
        """El score debe ser un número flotante."""
        from ml.modelo_territorial import compute_ivt_score

        score = compute_ivt_score(
            indice=110.0, variacion_mensual=1.0, variacion_anual=5.0,
            precipitacion=80.0, temperatura=22.0, mes=6, año=2024
        )
        assert isinstance(score, float)


# ── Tests de thresholds ────────────────────────────────────────────────────────

@pytest.mark.ml
class TestIvtThresholds:
    """Pruebas para los umbrales de clasificación."""

    def test_thresholds_are_calibrated(self):
        """Los thresholds deben estar en el rango esperado para datos reales."""
        from ml.modelo_territorial import THRESHOLD_MEDIA, THRESHOLD_ALTA

        assert 20.0 <= THRESHOLD_MEDIA <= 40.0, f"THRESHOLD_MEDIA={THRESHOLD_MEDIA} fuera de rango"
        assert 35.0 <= THRESHOLD_ALTA <= 60.0, f"THRESHOLD_ALTA={THRESHOLD_ALTA} fuera de rango"
        assert THRESHOLD_MEDIA < THRESHOLD_ALTA, "THRESHOLD_MEDIA debe ser menor que THRESHOLD_ALTA"

    def test_classification_labels_exist(self):
        """Las etiquetas de clasificación deben existir."""
        from ml.modelo_territorial import LABELS

        assert "BAJA" in LABELS
        assert "MEDIA" in LABELS
        assert "ALTA" in LABELS


# ── Tests del modelo entrenado (si existe) ─────────────────────────────────────

@pytest.mark.ml
@pytest.mark.slow
class TestModeloEntrenado:
    """Pruebas que requieren un modelo pre-entrenado."""

    def test_modelo_pkl_loads_correctly(self):
        """El modelo guardado debe cargar sin errores."""
        import os
        from pathlib import Path

        model_path = Path("ml/models/ivt_model.pkl")
        if not model_path.exists():
            pytest.skip("Modelo no entrenado. Ejecuta: make train")

        from ml.modelo_territorial import ModeloIVT
        modelo = ModeloIVT()
        modelo.load()
        assert modelo.clf is not None

    def test_modelo_predice_3_clases(self):
        """El modelo debe predecir las 3 clases: BAJA, MEDIA, ALTA."""
        import os
        from pathlib import Path

        model_path = Path("ml/models/ivt_model.pkl")
        if not model_path.exists():
            pytest.skip("Modelo no entrenado. Ejecuta: make train")

        from ml.modelo_territorial import ModeloIVT
        modelo = ModeloIVT()
        modelo.load()

        assert set(modelo.clf.classes_) == {"BAJA", "MEDIA", "ALTA"}, (
            f"Clases inesperadas: {modelo.clf.classes_}"
        )
