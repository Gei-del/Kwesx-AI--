"""
etl/transformers/normalize.py
==============================
Normalizadores: transforman los registros crudos de cada fuente al
Modelo Territorial Unificado (MTU) de Kwesx AI.

El MTU define una estructura común para cruzar datos de distintas fuentes:
  codigo_dane, departamento, municipio, latitud, longitud,
  fecha, sector, fuente + columnas específicas de cada dataset.

Cada normalizador es una clase con un método `transform(registros)` que
recibe una lista de dicts (output de los extractores) y retorna una lista
de dicts normalizados, listos para ser insertados en PostgreSQL.
"""

import re
from datetime import date, datetime
from loguru import logger

# ─────────────────────────────────────────────────────────────────────────────
# Lookup DANE: nombre_municipio_lower → codigo_dane (5 dígitos DIVIPOLA)
# Solo los municipios más frecuentes en los datasets IDEAM y ANI.
# Fuente: DIVIPOLA 2024 — DANE.
# ─────────────────────────────────────────────────────────────────────────────
DANE_LOOKUP: dict[str, str] = {
    # Antioquia
    "medellín": "05001", "medellin": "05001",
    "bello": "05088", "itagüí": "05360", "itagui": "05360",
    "envigado": "05266", "rionegro": "05615", "marinilla": "05440",
    "barbosa": "05079", "copacabana": "05212", "girardota": "05310",
    # Bogotá
    "bogotá": "11001", "bogota": "11001", "bogotá d.c.": "11001",
    # Valle del Cauca
    "cali": "76001", "buenaventura": "76113", "palmira": "76520",
    "tuluá": "76834", "tulua": "76834", "cartago": "76147",
    # Atlántico
    "barranquilla": "08001", "soledad": "08758",
    # Bolívar
    "cartagena": "13001", "turbana": "13780",
    # Cundinamarca
    "zipaquirá": "25899", "zipaquira": "25899",
    "chía": "25175", "chia": "25175", "cajicá": "25126", "cajica": "25126",
    "soacha": "25754", "tenjo": "25799", "facatativá": "25269",
    "facatativa": "25269",
    # Santander
    "bucaramanga": "68001", "floridablanca": "68276",
    "girón": "68307", "giron": "68307",
    # Norte de Santander
    "cúcuta": "54001", "cucuta": "54001",
    # Boyacá
    "tunja": "15001", "duitama": "15238", "sogamoso": "15759",
    # Caldas
    "manizales": "17001",
    # Risaralda
    "pereira": "66001", "dosquebradas": "66170",
    # Quindío
    "armenia": "63001",
    # Tolima
    "ibagué": "73001", "ibague": "73001",
    # Huila
    "neiva": "41001",
    # Nariño
    "pasto": "52001",
    # Cauca
    "popayán": "19001", "popayan": "19001",
    # Cesar
    "valledupar": "20001", "bosconia": "20060", "chimichagua": "20238",
    # Magdalena
    "santa marta": "47001", "ciénaga": "47189", "cienaga": "47189",
    "sevilla": "47660",
    # Córdoba
    "montería": "23001", "monteria": "23001",
    # Sucre
    "sincelejo": "70001",
    # Meta
    "villavicencio": "50001",
    # Casanare
    "yopal": "85001",
    # Arauca
    "arauca": "81001",
    # Putumayo
    "mocoa": "86001",
    # Amazonas
    "leticia": "91001",
    # Chocó
    "quibdó": "27001", "quibdo": "27001",
    # Guajira
    "riohacha": "44001",
}


def _parse_date(value: str | None) -> date | None:
    """Convierte un string de fecha a date. Maneja los formatos de Socrata."""
    if not value:
        return None
    # Formatos comunes de Socrata: '2024-01-15T00:00:00.000', '2024-01-15'
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:len(fmt) - 3] if "T" in value else value, fmt).date()
        except ValueError:
            continue
    logger.warning(f"No se pudo parsear fecha: {value!r}")
    return None


def _parse_float(value) -> float | None:
    """Convierte a float de forma segura."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_int(value) -> int | None:
    """Convierte a int de forma segura."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _get_dane(municipio: str | None) -> str | None:
    """Lookup DANE por nombre de municipio (insensible a mayúsculas/tildes)."""
    if not municipio:
        return None
    key = municipio.strip().lower()
    return DANE_LOOKUP.get(key)


# ─────────────────────────────────────────────────────────────────────────────
# ANI
# ─────────────────────────────────────────────────────────────────────────────

class ANINormalizer:
    """
    Transforma registros crudos de ANI al schema MTU.

    Input esperado (dict por registro):
      idpeaje, peaje, categoriatarifa, desde, hasta, valortarifa,
      cantidadtrafico, cantidadevasores, cantidadexentos787
      + campos de geolocalización agregados por ANIExtractor.enrich_with_location()

    Output (dict por registro):
      Todos los campos MTU + campos específicos de ANI.
    """

    SECTOR = "transporte"
    FUENTE = "ANI"

    def transform(self, registros: list[dict]) -> list[dict]:
        """Normaliza una lista de registros ANI."""
        result = []
        errores = 0
        for r in registros:
            try:
                norma = {
                    # MTU base
                    "codigo_dane":  r.get("codigo_dane"),
                    "departamento": r.get("departamento"),
                    "municipio":    r.get("municipio"),
                    "latitud":      _parse_float(r.get("latitud")),
                    "longitud":     _parse_float(r.get("longitud")),
                    "fecha":        _parse_date(r.get("desde")),
                    "sector":       self.SECTOR,
                    "fuente":       self.FUENTE,
                    # ANI específico
                    "idpeaje":          r.get("idpeaje"),
                    "peaje":            r.get("peaje"),
                    "categoria_tarifa": r.get("categoriatarifa"),
                    "fecha_inicio":     _parse_date(r.get("desde")),
                    "fecha_fin":        _parse_date(r.get("hasta")),
                    "valor_tarifa":     _parse_float(r.get("valortarifa")),
                    "cantidad_trafico": _parse_int(r.get("cantidadtrafico")),
                    "cantidad_evasores":_parse_int(r.get("cantidadevasores")),
                    "cantidad_exentos": _parse_int(r.get("cantidadexentos787")),
                }
                result.append(norma)
            except Exception as exc:
                errores += 1
                logger.debug(f"[ANI] Error normalizando registro: {exc}")

        if errores:
            logger.warning(f"[ANI] {errores} registros con error omitidos.")
        logger.info(f"[ANI] Normalizados: {len(result)} registros.")
        return result


# ─────────────────────────────────────────────────────────────────────────────
# UPRA
# ─────────────────────────────────────────────────────────────────────────────

class UPRANormalizer:
    """
    Transforma registros crudos de UPRA al schema MTU.

    UPRA es un índice nacional, sin coordenadas por municipio.
    Se asigna codigo_dane = '00' (Colombia nacional, convenio Kwesx AI).
    """

    SECTOR = "agropecuario"
    FUENTE = "UPRA"
    CODIGO_NACIONAL = "00"

    def transform(self, registros: list[dict]) -> list[dict]:
        """Normaliza una lista de registros UPRA."""
        result = []
        errores = 0
        for r in registros:
            try:
                norma = {
                    # MTU base
                    "codigo_dane":  self.CODIGO_NACIONAL,
                    "departamento": "Nacional",
                    "municipio":    "Colombia",
                    "latitud":      4.5709,   # centroide de Colombia
                    "longitud":     -74.2973,
                    "fecha":        _parse_date(r.get("fecha")),
                    "sector":       self.SECTOR,
                    "fuente":       self.FUENTE,
                    # UPRA específico
                    "indice_total":         _parse_float(r.get("indice_total")),
                    "total_fertilizantes":  _parse_float(r.get("total_fertilizantes")),
                    "total_plaguicidas":    _parse_float(r.get("total_plaguicidas")),
                    "total_otros":          _parse_float(r.get("total_otros")),
                }
                result.append(norma)
            except Exception as exc:
                errores += 1
                logger.debug(f"[UPRA] Error normalizando registro: {exc}")

        if errores:
            logger.warning(f"[UPRA] {errores} registros con error omitidos.")
        logger.info(f"[UPRA] Normalizados: {len(result)} registros.")
        return result


# ─────────────────────────────────────────────────────────────────────────────
# IDEAM
# ─────────────────────────────────────────────────────────────────────────────

class IDEAMNormalizer:
    """
    Transforma registros crudos de IDEAM (precipitación + temperatura) al MTU.

    Los datasets IDEAM incluyen Departamento y Municipio como texto.
    Se usa el DANE_LOOKUP para agregar codigo_dane donde sea posible.
    """

    SECTOR = "climatico"
    FUENTE = "IDEAM"

    def transform(self, registros: list[dict]) -> list[dict]:
        """Normaliza una lista de registros IDEAM (cualquier variable)."""
        result = []
        sin_dane = 0
        errores = 0
        for r in registros:
            try:
                municipio = r.get("municipio") or r.get("Municipio")
                departamento = r.get("departamento") or r.get("Departamento")
                codigo_dane = _get_dane(municipio)
                if not codigo_dane:
                    sin_dane += 1

                norma = {
                    # MTU base
                    "codigo_dane":  codigo_dane,
                    "departamento": departamento,
                    "municipio":    municipio,
                    "latitud":      _parse_float(r.get("latitud") or r.get("Latitud")),
                    "longitud":     _parse_float(r.get("longitud") or r.get("Longitud")),
                    "fecha":        _parse_date(
                        r.get("fechaobservacion") or r.get("FechaObservacion")
                    ),
                    "sector":       self.SECTOR,
                    "fuente":       self.FUENTE,
                    # IDEAM específico
                    "codigo_estacion": r.get("codigoestacion") or r.get("CodigoEstacion"),
                    "nombre_estacion": r.get("nombreestacion") or r.get("NombreEstacion"),
                    "codigo_sensor":   r.get("codigosensor") or r.get("CodigoSensor"),
                    "tipo_variable":   r.get("tipo_variable"),
                    "valor_observado": _parse_float(
                        r.get("valorobservado") or r.get("ValorObservado")
                    ),
                    "unidad_medida":   r.get("unidadmedida") or r.get("UnidadMedida"),
                    "zona_hidrografica": r.get("zonahidrografica") or r.get("ZonaHidrografica"),
                }
                result.append(norma)
            except Exception as exc:
                errores += 1
                logger.debug(f"[IDEAM] Error normalizando registro: {exc}")

        if sin_dane:
            logger.warning(f"[IDEAM] {sin_dane} registros sin código DANE (municipio no mapeado).")
        if errores:
            logger.warning(f"[IDEAM] {errores} registros con error omitidos.")
        logger.info(f"[IDEAM] Normalizados: {len(result)} registros.")
        return result
