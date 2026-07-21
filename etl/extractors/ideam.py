"""
etl/extractors/ideam.py
=======================
Extractor para los datasets IDEAM — Variables Climáticas.

Usamos 2 datasets complementarios de la "Oficina de Informática IDEAM":
1. Precipitación       (s54a-sgyg) — mm de lluvia cada 10 min, actualizado diariamente
2. Temperatura Ambiente (sbwg-7ju4) — °C cada hora, actualizado diariamente

Ambos tienen exactamente el mismo schema:
-----------------------------------------
CodigoSensor       — ID del sensor en la estación
ValorObservado     — valor medido (mm ó °C según el dataset)
ZonaHidrografica   — cuenca hidrográfica
CodigoEstacion     — ID de la estación IDEAM
Departamento       — nombre del departamento (texto)
Latitud            — latitud decimal
DescripcionSensor  — descripción del tipo de sensor
NombreEstacion     — nombre de la estación
FechaObservacion   — fecha y hora de la medición
Municipio          — nombre del municipio (texto)
UnidadMedida       — 'Milimetros' ó 'Grados centigrados'
Longitud           — longitud decimal

Nota sobre DANE
---------------
El IDEAM usa Departamento y Municipio como texto, no código DANE.
Para el MTU hacemos JOIN con la tabla de DANE lookup que incluimos en
etl/transformers/normalize.py. Las estaciones con nombres no reconocidos
quedan con codigo_dane = NULL.

Nota sobre volumen
------------------
Estas tablas son masivas (millones de filas). Para el MVP cargamos
solo los últimos N días configurables (default: 30 días).
La carga histórica completa se hace en un paso aparte si el tiempo lo permite.
"""

from loguru import logger
from .base import SocrataExtractor
from etl.config import (
    IDEAM_PRECIPITACION_ID,
    IDEAM_TEMPERATURA_ID,
    IDEAM_CATALOGO_ID,
)

# Columnas del schema compartido de los datasets IDEAM
IDEAM_COLS = [
    "codigoestacion",
    "nombreestacion",
    "codigosensor",
    "descripcionsensor",
    "departamento",
    "municipio",
    "latitud",
    "longitud",
    "zonahidrografica",
    "fechaobservacion",
    "valorobservado",
    "unidadmedida",
]


class IDEAMExtractor:
    """
    Extractor para variables climáticas del IDEAM.

    Agrupa los dos datasets (precipitación y temperatura) bajo una
    interfaz unificada, añadiendo el campo `tipo_variable` para
    distinguir las mediciones en la tabla MTU.

    Uso
    ---
    from etl.extractors.ideam import IDEAMExtractor

    ext = IDEAMExtractor()
    registros = ext.fetch_recent(dias=30)   # últimos 30 días, ambas variables
    prec = ext.fetch_precipitacion(dias=7)  # solo lluvia, últimos 7 días
    temp = ext.fetch_temperatura(dias=7)    # solo temperatura, últimos 7 días
    """

    def __init__(self):
        self._prec = _IDEAMSingleExtractor(
            dataset_id=IDEAM_PRECIPITACION_ID,
            nombre="IDEAM Precipitación",
            tipo_variable="precipitacion_mm",
        )
        self._temp = _IDEAMSingleExtractor(
            dataset_id=IDEAM_TEMPERATURA_ID,
            nombre="IDEAM Temperatura",
            tipo_variable="temperatura_c",
        )
        self._catalogo = _CatalogoEstacionesExtractor()

    def fetch_recent(self, dias: int = 30) -> list[dict]:
        """
        Descarga los últimos `dias` días de precipitación + temperatura.
        Retorna una lista combinada con tipo_variable como discriminador.
        """
        import datetime
        fecha_inicio = (
            datetime.date.today() - datetime.timedelta(days=dias)
        ).isoformat()

        logger.info(f"[IDEAM] Descargando datos desde {fecha_inicio} ({dias} días)...")

        prec = self._prec.fetch_from(fecha_inicio)
        temp = self._temp.fetch_from(fecha_inicio)

        logger.info(
            f"[IDEAM] Precipitación: {len(prec)} registros | "
            f"Temperatura: {len(temp)} registros"
        )
        return prec + temp

    def fetch_precipitacion(self, dias: int = 30) -> list[dict]:
        """Descarga solo precipitación de los últimos `dias` días."""
        import datetime
        fecha_inicio = (
            datetime.date.today() - datetime.timedelta(days=dias)
        ).isoformat()
        return self._prec.fetch_from(fecha_inicio)

    def fetch_temperatura(self, dias: int = 30) -> list[dict]:
        """Descarga solo temperatura de los últimos `dias` días."""
        import datetime
        fecha_inicio = (
            datetime.date.today() - datetime.timedelta(days=dias)
        ).isoformat()
        return self._temp.fetch_from(fecha_inicio)

    def fetch_catalogo(self) -> list[dict]:
        """
        Descarga el catálogo de estaciones IDEAM.
        Útil para enriquecer los datos con código DANE por municipio.
        """
        return self._catalogo.fetch_all()


# ─────────────────────────────────────────────────────────────────────────────
# Clases internas
# ─────────────────────────────────────────────────────────────────────────────

class _IDEAMSingleExtractor(SocrataExtractor):
    """Extractor para un dataset IDEAM individual (precipitación O temperatura)."""

    def __init__(self, dataset_id: str, nombre: str, tipo_variable: str):
        super().__init__(dataset_id=dataset_id, nombre=nombre)
        self.tipo_variable = tipo_variable

    def fetch_from(self, fecha_inicio: str) -> list[dict]:
        """
        Descarga mediciones desde fecha_inicio.
        Agrega el campo tipo_variable a cada registro.
        """
        registros = self.fetch_all(
            where=f"fechaobservacion >= '{fecha_inicio}T00:00:00.000'",
            select=", ".join(IDEAM_COLS),
            order="fechaobservacion",
        )
        # Agregar discriminador de variable
        for r in registros:
            r["tipo_variable"] = self.tipo_variable
        return registros


class _CatalogoEstacionesExtractor(SocrataExtractor):
    """Extractor para el catálogo de estaciones IDEAM (lookup de DANE codes)."""

    def __init__(self):
        super().__init__(
            dataset_id=IDEAM_CATALOGO_ID,
            nombre="IDEAM Catálogo Estaciones",
        )

    def fetch_all(self) -> list[dict]:  # type: ignore[override]
        return super().fetch_all(
            select="codigo, nombre, departamento, municipio, latitud, longitud, estado",
            order="codigo",
        )
