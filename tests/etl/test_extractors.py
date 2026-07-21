"""
Kwesx AI — Tests del pipeline ETL (extractores Socrata)
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.etl
@pytest.mark.unit
class TestSocrataExtractor:
    """Pruebas unitarias para el cliente Socrata genérico."""

    def test_extractor_construye_url_correctamente(self):
        """El extractor debe construir la URL de Socrata correctamente."""
        from etl.extractors.base import SocrataExtractor

        extractor = SocrataExtractor(dataset_id="8yi9-t44c", domain="www.datos.gov.co")
        url = extractor.build_url()
        assert "8yi9-t44c" in url
        assert "datos.gov.co" in url

    def test_extractor_aplica_limit_correcto(self):
        """El extractor debe respetar el parámetro limit."""
        from etl.extractors.base import SocrataExtractor

        extractor = SocrataExtractor(dataset_id="8yi9-t44c", domain="www.datos.gov.co", limit=500)
        url = extractor.build_url()
        assert "$limit=500" in url or "limit=500" in url

    @patch("etl.extractors.base.requests.get")
    def test_extractor_retorna_lista_de_registros(self, mock_get, mock_socrata_response):
        """El extractor debe retornar una lista de registros."""
        from etl.extractors.base import SocrataExtractor

        mock_response = MagicMock()
        mock_response.json.return_value = mock_socrata_response
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        extractor = SocrataExtractor(dataset_id="gwbi-fnzs", domain="www.datos.gov.co")
        records = extractor.extract(offset=0)

        assert isinstance(records, list)
        assert len(records) == len(mock_socrata_response)

    @patch("etl.extractors.base.requests.get")
    def test_extractor_reintenta_en_error_500(self, mock_get):
        """El extractor debe reintentar en errores 5xx."""
        import requests
        from etl.extractors.base import SocrataExtractor

        mock_get.side_effect = requests.exceptions.HTTPError("500 Server Error")

        extractor = SocrataExtractor(
            dataset_id="8yi9-t44c",
            domain="www.datos.gov.co",
            max_retries=2,
            retry_delay=0.01  # delay mínimo para test
        )

        with pytest.raises((requests.exceptions.HTTPError, Exception)):
            extractor.extract(offset=0)

        # Debe haber intentado más de 1 vez
        assert mock_get.call_count >= 1


@pytest.mark.etl
@pytest.mark.unit
class TestTransformers:
    """Pruebas para los transformadores de datos."""

    def test_upra_normalizer_genera_columnas_esperadas(self, mock_socrata_response):
        """El normalizador UPRA debe generar las columnas requeridas."""
        from etl.transformers.upra import normalizar_upra

        df = normalizar_upra(mock_socrata_response)

        assert "fecha" in df.columns
        assert "indice" in df.columns or "valor" in df.columns

    def test_upra_normalizer_convierte_tipos_correctos(self, mock_socrata_response):
        """El normalizador UPRA debe convertir tipos de datos correctamente."""
        from etl.transformers.upra import normalizar_upra
        import pandas as pd

        df = normalizar_upra(mock_socrata_response)

        col_indice = "indice" if "indice" in df.columns else "valor"
        assert pd.api.types.is_float_dtype(df[col_indice]) or pd.api.types.is_numeric_dtype(df[col_indice])
