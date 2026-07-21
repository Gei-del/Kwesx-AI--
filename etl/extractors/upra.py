"""
etl/extractors/upra.py
======================
Extractor para el dataset UPRA — Índice de Precios de Insumos Agrícolas.

Dataset: https://www.datos.gov.co/d/gwbi-fnzs
ID Socrata: gwbi-fnzs
Registros: 89 (serie mensual enero 2021 — junio 2026)
Frecuencia: mensual

Columnas principales del dataset original (57 en total)
---------------------------------------------------------
fecha                   — primer día del mes (YYYY-MM-DDT00:00:00.000)
indice_total            — índice agregado de todos los insumos
total_fertilizantes     — subíndice fertilizantes
total_plaguicidas       — subíndice plaguicidas (herbicidas + fungicidas + insecticidas)
total_otros             — otros insumos
... (subíndices individuales por insumo)

Nota de cobertura geográfica
-----------------------------
UPRA es un índice NACIONAL. No hay desglose por departamento ni municipio.
En el MTU se almacena con codigo_dane = '00' (código convenido para Colombia nacional).
Sí tiene dimensión temporal (fecha mensual), que es su principal variable de análisis.
"""

from .base import SocrataExtractor
from etl.config import UPRA_DATASET_ID

# Columnas UPRA que nos interesan para el MVP.
# Mantenemos el índice total + los 3 subgrupos principales.
# Si más adelante se necesitan los subíndices individuales, se agregan aquí.
UPRA_COLS_MVP = [
    "fecha",
    "indice_total",
    "total_fertilizantes",
    "total_plaguicidas",
    "total_otros",
]


class UPRAExtractor(SocrataExtractor):
    """
    Extractor específico para el dataset UPRA de precios de insumos agrícolas.

    Uso
    ---
    from etl.extractors.upra import UPRAExtractor

    ext = UPRAExtractor()
    registros = ext.fetch_all_raw()       # las 89 filas completas
    registros = ext.fetch_mvp()           # solo las columnas del MVP
    """

    def __init__(self):
        super().__init__(
            dataset_id=UPRA_DATASET_ID,
            nombre="UPRA Insumos Agrícolas",
        )

    def fetch_all_raw(self) -> list[dict]:
        """
        Descarga las 89 filas completas (las 57 columnas del dataset).
        """
        return self.fetch_all(order="fecha")

    def fetch_mvp(self) -> list[dict]:
        """
        Descarga solo las columnas del MVP ordenadas por fecha.
        Más rápido y suficiente para el dashboard principal.
        """
        return self.fetch_all(
            select=", ".join(UPRA_COLS_MVP),
            order="fecha",
        )

    def fetch_from(self, fecha_inicio: str) -> list[dict]:
        """
        Descarga registros a partir de una fecha dada.
        fecha_inicio: str en formato 'YYYY-MM-DD'
        """
        return self.fetch_all(
            where=f"fecha >= '{fecha_inicio}'",
            order="fecha",
        )
