"""
Kwesx AI — Fixtures compartidas para pruebas
"""

import pytest
import pandas as pd
from unittest.mock import AsyncMock, MagicMock


# ── Fixtures de datos de prueba ────────────────────────────────────────────────

@pytest.fixture
def sample_upra_df():
    """DataFrame de ejemplo con estructura UPRA (precios insumos agrícolas)."""
    return pd.DataFrame({
        "fecha": pd.date_range("2024-01", periods=12, freq="MS"),
        "periodo": [f"2024-{i:02d}" for i in range(1, 13)],
        "indice": [110.2, 111.5, 113.0, 115.2, 116.8, 114.5,
                   113.2, 112.8, 114.1, 116.3, 117.9, 119.2],
        "variacion_mensual": [0.8, 1.2, 1.3, 1.9, 1.4, -2.0,
                              -1.1, -0.4, 1.1, 1.9, 1.4, 1.1],
        "variacion_anual": [5.2, 5.8, 6.1, 6.5, 6.8, 5.9,
                            4.8, 4.2, 4.5, 5.1, 5.6, 5.9],
        "categoria": ["FERTILIZANTES"] * 6 + ["SEMILLAS"] * 6,
    })


@pytest.fixture
def sample_ani_df():
    """DataFrame de ejemplo con estructura ANI (peajes/tráfico)."""
    return pd.DataFrame({
        "fecha": pd.date_range("2024-01-01", periods=30, freq="D"),
        "peaje": ["PEAJE EL VINO"] * 10 + ["PEAJE BUENAVISTA"] * 10 + ["PEAJE LA PAILA"] * 10,
        "concesion": ["CONCESION A"] * 10 + ["CONCESION B"] * 10 + ["CONCESION C"] * 10,
        "tipo_vehiculo": ["AUTOMOVILES", "BUSES", "CAMIONES"] * 10,
        "cantidad": [1200, 450, 380, 1350, 490, 410, 1100, 400, 350,
                     1250, 200, 150, 180, 220, 170, 195, 210, 160,
                     175, 190, 800, 850, 820, 790, 810, 840, 830, 800, 815, 790],
        "departamento": ["CUNDINAMARCA"] * 10 + ["BOLÍVAR"] * 10 + ["VALLE DEL CAUCA"] * 10,
    })


@pytest.fixture
def sample_ivt_features():
    """Features de ejemplo para el modelo IVT."""
    return pd.DataFrame({
        "periodo": ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05",
                    "2024-06", "2024-07", "2024-08", "2024-09", "2024-10"],
        "upra_indice": [110.2, 111.5, 113.0, 115.2, 116.8, 114.5, 113.2, 112.8, 114.1, 116.3],
        "upra_variacion_mensual": [0.8, 1.2, 1.3, 1.9, 1.4, -2.0, -1.1, -0.4, 1.1, 1.9],
        "upra_variacion_anual": [5.2, 5.8, 6.1, 6.5, 6.8, 5.9, 4.8, 4.2, 4.5, 5.1],
        "clima_precipitacion": [45.2, 62.1, 98.3, 145.6, 132.4, 88.7, 67.3, 78.9, 112.4, 140.2],
        "clima_temperatura": [22.1, 22.5, 23.0, 22.8, 22.3, 23.1, 23.5, 23.2, 22.9, 22.6],
        "mes": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "año": [2024] * 10,
    })


# ── Fixtures de mocks ──────────────────────────────────────────────────────────

@pytest.fixture
def mock_db_session():
    """Mock de sesión de base de datos SQLAlchemy async."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_socrata_response():
    """Mock de respuesta de la API Socrata."""
    return [
        {
            "fecha": "2024-01-01T00:00:00",
            "indice": "110.2",
            "variacion_mensual": "0.8",
            "categoria": "FERTILIZANTES",
        },
        {
            "fecha": "2024-02-01T00:00:00",
            "indice": "111.5",
            "variacion_mensual": "1.2",
            "categoria": "FERTILIZANTES",
        },
    ]
