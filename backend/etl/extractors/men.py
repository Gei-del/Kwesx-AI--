"""
backend/etl/extractors/men.py
================================
ETL para datos de Cobertura Educativa por municipio.

Fuentes
-------
- MEN -- SIMAT (Sistema Integrado de Matricula)
  Matriculados y tasas de cobertura por municipio, nivel y zona.
  URL: https://www.datos.gov.co/resource/nudc-7mev.json  (Estadisticas Educacion Preescolar)

Como el SIMAT tiene multiples datasets por nivel educativo, este ETL
consolida los datos de los niveles: preescolar, primaria, secundaria y media.

Si la API no esta disponible, genera datos sinteticos basados en los
promedios reales del DANE ECV 2023 y los reportes MEN 2022.

Uso
---
  python -m backend.etl.extractors.men
"""

from __future__ import annotations

import logging
import random
from datetime import date
from typing import Any

import requests

logger = logging.getLogger(__name__)

# -- Configuracion Socrata API ------------------------------------------------
BASE_URL = "https://www.datos.gov.co/resource"
# MEN publica multiples datasets; usamos el consolidado de estadisticas
RESOURCE_MEN_COBERTURA = "nudc-7mev"
TIMEOUT = 30


# -- Tasas de referencia por departamento (MEN 2022) --------------------------
# Tasa neta de cobertura (%) por nivel y departamento
_REF_COBERTURA: dict[str, dict] = {
    "Bogota D.C.":  {"preescolar": 62.1, "primaria": 95.4, "secundaria": 82.3, "media": 48.7},
    "Antioquia":    {"preescolar": 58.4, "primaria": 93.2, "secundaria": 79.1, "media": 44.3},
    "Valle":        {"preescolar": 55.8, "primaria": 91.8, "secundaria": 76.4, "media": 41.2},
    "Cundinamarca": {"preescolar": 54.2, "primaria": 90.7, "secundaria": 74.8, "media": 39.6},
    "Santander":    {"preescolar": 53.1, "primaria": 89.4, "secundaria": 73.2, "media": 38.1},
    "Atlantico":    {"preescolar": 51.7, "primaria": 88.9, "secundaria": 71.6, "media": 36.8},
    "Boyaca":       {"preescolar": 48.3, "primaria": 87.2, "secundaria": 68.4, "media": 33.2},
    "Tolima":       {"preescolar": 47.1, "primaria": 86.8, "secundaria": 67.1, "media": 31.9},
    "Huila":        {"preescolar": 46.4, "primaria": 86.1, "secundaria": 65.8, "media": 30.7},
    "Narino":       {"preescolar": 43.8, "primaria": 84.3, "secundaria": 61.2, "media": 27.4},
    "Cauca":        {"preescolar": 42.1, "primaria": 83.7, "secundaria": 59.8, "media": 25.6},
    "Choco":        {"preescolar": 36.4, "primaria": 78.2, "secundaria": 48.3, "media": 18.9},
    "_default":     {"preescolar": 48.0, "primaria": 87.0, "secundaria": 68.0, "media": 34.0},
}

_MUNICIPIOS_MUESTRA: list[tuple[str, str, str]] = [
    ("05001", "Medellin",       "Antioquia"),
    ("05615", "Rionegro",       "Antioquia"),
    ("05088", "Bello",          "Antioquia"),
    ("11001", "Bogota D.C.",    "Bogota D.C."),
    ("76001", "Cali",           "Valle"),
    ("08001", "Barranquilla",   "Atlantico"),
    ("13001", "Cartagena",      "Bolivar"),
    ("68001", "Bucaramanga",    "Santander"),
    ("25754", "Soacha",         "Cundinamarca"),
    ("15001", "Tunja",          "Boyaca"),
    ("73001", "Ibague",         "Tolima"),
    ("41001", "Neiva",          "Huila"),
    ("52001", "Pasto",          "Narino"),
    ("19001", "Popayan",        "Cauca"),
    ("27001", "Quibdo",         "Choco"),
    ("50001", "Villavicencio",  "Meta"),
    ("17001", "Manizales",      "Caldas"),
    ("63001", "Armenia",        "Quindio"),
    ("66001", "Pereira",        "Risaralda"),
]


def extraer_educacion(
    app_token: str = "",
    anio: int = 2022,
    limit: int = 2000,
) -> list[dict[str, Any]]:
    """
    Descarga datos de cobertura educativa del MEN (datos.gov.co).
    Si la descarga falla, retorna datos sinteticos.
    """
    try:
        url = f"{BASE_URL}/{RESOURCE_MEN_COBERTURA}.json"
        headers = {}
        if app_token:
            headers["X-App-Token"] = app_token

        resp = requests.get(url, headers=headers, timeout=TIMEOUT, params={
            "$limit": limit,
        })
        resp.raise_for_status()
        raw = resp.json()

        registros = _transformar_educacion(raw, anio)
        if registros:
            logger.info(f"Educacion descargada: {len(registros)} registros")
            return registros

    except Exception as e:
        logger.warning(f"No se pudo descargar datos MEN ({e}). Usando datos de referencia.")

    return _generar_datos_sinteticos_educacion(anio)


def _transformar_educacion(raw: list[dict], anio: int) -> list[dict]:
    """Mapea la estructura del SIMAT al esquema MTU."""
    registros = []
    for row in raw:
        try:
            dane  = str(row.get("codigo_dane_municipio") or row.get("cod_mpio") or "").strip()
            depto = (row.get("departamento") or "").strip()
            mun   = (row.get("municipio") or "").strip()
            nivel = (row.get("nivel") or row.get("nivel_educativo") or "total").lower().strip()

            matriculados = int(row.get("total_matriculados") or row.get("matriculados") or 0)
            cobertura    = float(row.get("tasa_cobertura_neta") or 0)

            if not dane or not mun:
                continue

            registros.append({
                "codigo_dane":           dane,
                "departamento":          depto,
                "municipio":             mun,
                "latitud":               None,
                "longitud":              None,
                "anio":                  anio,
                "fecha":                 date(anio, 12, 31).isoformat(),
                "nivel_educativo":       nivel,
                "matriculados":          matriculados,
                "matriculados_oficial":  int(row.get("matriculados_oficial") or 0) or None,
                "matriculados_privado":  int(row.get("matriculados_no_oficial") or 0) or None,
                "tasa_cobertura_neta":   round(cobertura, 2),
                "tasa_cobertura_bruta":  float(row.get("tasa_cobertura_bruta") or 0) or None,
                "tasa_aprobacion":       float(row.get("tasa_aprobacion") or 0) or None,
                "tasa_desercion":        float(row.get("tasa_desercion") or 0) or None,
                "zona":                  row.get("zona", "total"),
                "sector":                "educacion",
                "fuente":                "MEN-SIMAT",
            })
        except (ValueError, TypeError, KeyError):
            continue

    return registros


def _generar_datos_sinteticos_educacion(anio: int) -> list[dict]:
    """
    Genera datos de cobertura educativa basados en los promedios MEN 2022.
    """
    random.seed(123)
    registros = []
    niveles = ["preescolar", "primaria", "secundaria", "media"]

    for dane, nombre, depto in _MUNICIPIOS_MUESTRA:
        ref = _REF_COBERTURA.get(depto, _REF_COBERTURA["_default"])

        for nivel in niveles:
            base_cobertura = ref[nivel]
            jitter = lambda b: round(max(0, min(100, b + random.uniform(-7, 7))), 1)

            cobertura_neta   = jitter(base_cobertura)
            cobertura_bruta  = jitter(base_cobertura + random.uniform(8, 20))
            tasa_aprobacion  = jitter(85 + random.uniform(-10, 8))
            tasa_desercion   = round(max(0, min(20, random.uniform(2, 12))), 1)

            # Estimacion de matriculados (proporcional al nivel)
            peso = {"preescolar": 0.12, "primaria": 0.45, "secundaria": 0.28, "media": 0.15}
            base_mat = random.randint(5000, 200000)
            matriculados = int(base_mat * peso.get(nivel, 0.25))

            registros.append({
                "codigo_dane":           dane,
                "departamento":          depto,
                "municipio":             nombre,
                "latitud":               None,
                "longitud":              None,
                "anio":                  anio,
                "fecha":                 date(anio, 12, 31).isoformat(),
                "nivel_educativo":       nivel,
                "matriculados":          matriculados,
                "matriculados_oficial":  int(matriculados * random.uniform(0.65, 0.90)),
                "matriculados_privado":  int(matriculados * random.uniform(0.10, 0.35)),
                "tasa_cobertura_neta":   cobertura_neta,
                "tasa_cobertura_bruta":  cobertura_bruta,
                "tasa_aprobacion":       tasa_aprobacion,
                "tasa_desercion":        tasa_desercion,
                "zona":                  "total",
                "sector":                "educacion",
                "fuente":                "MEN-SIMAT-SIMULADO",
            })

    logger.info(f"Datos sinteticos MEN generados: {len(registros)} registros")
    return registros


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    datos = extraer_educacion()
    print(f"Total registros: {len(datos)}")
    if datos:
        print("Primeros 3:")
        for d in datos[:3]:
            print(" ", d)
