"""
backend/etl/extractors/dane_mintic.py
=======================================
ETL para datos de Conectividad a Internet por municipio.

Fuentes
-------
- DANE Encuesta de Calidad de Vida (ECV) -- hogares con acceso a internet
  URL: https://www.datos.gov.co/resource/ds9f-k39s.json  (ejemplo ECV)
- MinTIC -- Indice de Penetracion de Internet Fijo por municipio
  URL: https://www.datos.gov.co/resource/ghgs-xx6j.json

Como los datasets de conectividad en datos.gov.co tienen estructura
variable por ano, este ETL:
  1. Intenta descargar del endpoint oficial.
  2. Si falla, genera datos sinteticos realistas basados en promedios
     departamentales de la ECV 2023 para no bloquear el sistema.

Los datos sinteticos son utiles en demos/hackathons cuando la API
no esta disponible. Se marcan con fuente='DANE-MinTIC-SIMULADO'.

Uso
---
  python -m backend.etl.extractors.dane_mintic
"""

from __future__ import annotations

import logging
import random
from datetime import date, timedelta
from typing import Any

import requests

logger = logging.getLogger(__name__)

# -- Configuracion Socrata API ------------------------------------------------
BASE_URL   = "https://www.datos.gov.co/resource"
RESOURCE_CONECTIVIDAD = "ghgs-xx6j"   # MinTIC Internet Fijo Municipal
APP_TOKEN  = ""                        # sobreescrito desde settings si disponible
TIMEOUT    = 30


# -- Datos de referencia departamental (ECV 2023 aproximado) ------------------
# Porcentaje de hogares con acceso a internet por departamento
# Fuente: DANE ECV 2023 tabla 1.3
_REFERENCIA_DEPARTAMENTAL: dict[str, dict] = {
    "Bogota D.C.":  {"pct_internet": 78.2, "pct_celular": 95.1, "pct_pc": 52.3},
    "Antioquia":    {"pct_internet": 62.4, "pct_celular": 92.8, "pct_pc": 38.7},
    "Valle":        {"pct_internet": 61.1, "pct_celular": 91.5, "pct_pc": 37.2},
    "Cundinamarca": {"pct_internet": 55.8, "pct_celular": 89.3, "pct_pc": 32.1},
    "Santander":    {"pct_internet": 54.3, "pct_celular": 88.7, "pct_pc": 30.8},
    "Atlantico":    {"pct_internet": 52.1, "pct_celular": 89.2, "pct_pc": 28.4},
    "Boyaca":       {"pct_internet": 44.2, "pct_celular": 85.6, "pct_pc": 22.1},
    "Tolima":       {"pct_internet": 43.8, "pct_celular": 84.9, "pct_pc": 21.7},
    "Huila":        {"pct_internet": 42.5, "pct_celular": 83.2, "pct_pc": 20.3},
    "Narino":       {"pct_internet": 35.6, "pct_celular": 80.1, "pct_pc": 15.8},
    "Cauca":        {"pct_internet": 33.2, "pct_celular": 78.4, "pct_pc": 14.2},
    "Choco":        {"pct_internet": 21.3, "pct_celular": 68.7, "pct_pc":  8.4},
    "Vaupes":       {"pct_internet": 12.4, "pct_celular": 55.3, "pct_pc":  4.1},
    # Default para departamentos no listados
    "_default":     {"pct_internet": 40.0, "pct_celular": 82.0, "pct_pc": 18.0},
}

# Muestra de municipios para datos sinteticos (codigo_dane, nombre, departamento)
_MUNICIPIOS_MUESTRA: list[tuple[str, str, str]] = [
    ("05001", "Medellin",       "Antioquia"),
    ("05615", "Rionegro",       "Antioquia"),
    ("05088", "Bello",          "Antioquia"),
    ("11001", "Bogota D.C.",    "Bogota D.C."),
    ("76001", "Cali",           "Valle"),
    ("76520", "Palmira",        "Valle"),
    ("08001", "Barranquilla",   "Atlantico"),
    ("13001", "Cartagena",      "Bolivar"),
    ("68001", "Bucaramanga",    "Santander"),
    ("25001", "Agua de Dios",   "Cundinamarca"),
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


def extraer_conectividad(
    app_token: str = APP_TOKEN,
    anio: int = 2023,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """
    Descarga datos de conectividad municipal desde datos.gov.co.
    Si la descarga falla, retorna datos sinteticos marcados adecuadamente.
    """
    try:
        url = f"{BASE_URL}/{RESOURCE_CONECTIVIDAD}.json"
        headers = {}
        if app_token:
            headers["X-App-Token"] = app_token

        resp = requests.get(url, headers=headers, timeout=TIMEOUT, params={
            "$limit": limit,
            "$order": "municipio ASC",
        })
        resp.raise_for_status()
        raw = resp.json()

        registros = _transformar_conectividad(raw, anio)
        if registros:
            logger.info(f"Conectividad descargada: {len(registros)} registros")
            return registros

    except Exception as e:
        logger.warning(f"No se pudo descargar conectividad ({e}). Usando datos de referencia.")

    # Fallback: datos sinteticos basados en ECV 2023
    return _generar_datos_sinteticos_conectividad(anio)


def _transformar_conectividad(raw: list[dict], anio: int) -> list[dict]:
    """Mapea la estructura de la API de MinTIC al esquema MTU."""
    registros = []
    for row in raw:
        try:
            depto = (row.get("departamento") or row.get("nombre_departamento") or "").strip()
            mun   = (row.get("municipio")    or row.get("nombre_municipio")    or "").strip()
            dane  = str(row.get("codigo_dane") or row.get("cod_dane") or "00000").strip()
            pct   = float(row.get("indice_penetracion") or row.get("pct_hogares_internet") or 0)

            if not mun or pct == 0:
                continue

            registros.append({
                "codigo_dane":         dane,
                "departamento":        depto,
                "municipio":           mun,
                "latitud":             float(row.get("latitud")  or 0) or None,
                "longitud":            float(row.get("longitud") or 0) or None,
                "anio":                anio,
                "fecha":               date(anio, 12, 31).isoformat(),
                "pct_hogares_internet": round(pct, 2),
                "pct_hogares_celular":  float(row.get("pct_celular") or 0) or None,
                "pct_hogares_pc":       float(row.get("pct_pc") or 0) or None,
                "tipo_conexion":        row.get("tipo_conexion", "mixta"),
                "velocidad_mbps":       float(row.get("velocidad_promedio") or 0) or None,
                "poblacion":            int(row.get("poblacion") or 0) or None,
                "zona":                 row.get("zona", "total"),
                "sector":               "tecnologia",
                "fuente":               "MinTIC",
            })
        except (ValueError, TypeError, KeyError):
            continue

    return registros


def _generar_datos_sinteticos_conectividad(anio: int) -> list[dict]:
    """
    Genera datos de conectividad basados en promedios reales del DANE ECV 2023.
    Incluidos para no bloquear el sistema en demos sin acceso a la API.
    """
    random.seed(42)  # reproducible
    registros = []

    for dana, nombre, depto in _MUNICIPIOS_MUESTRA:
        ref = _REFERENCIA_DEPARTAMENTAL.get(depto, _REFERENCIA_DEPARTAMENTAL["_default"])

        # Variacion realista por municipio (+-8 puntos porcentuales)
        jitter = lambda base: round(max(0, min(100, base + random.uniform(-8, 8))), 1)

        for zona in ("urbana", "rural"):
            # Brecha urbano-rural tipica Colombia: rural = urbana * 0.4
            factor_rural = 0.42 if zona == "rural" else 1.0
            registros.append({
                "codigo_dane":         dana,
                "departamento":        depto,
                "municipio":           nombre,
                "latitud":             None,
                "longitud":            None,
                "anio":                anio,
                "fecha":               date(anio, 12, 31).isoformat(),
                "pct_hogares_internet": jitter(ref["pct_internet"] * factor_rural),
                "pct_hogares_celular":  jitter(ref["pct_celular"] * (0.8 if zona == "rural" else 1.0)),
                "pct_hogares_pc":       jitter(ref["pct_pc"] * factor_rural),
                "tipo_conexion":        "movil" if zona == "rural" else "mixta",
                "velocidad_mbps":       round(random.uniform(2, 10) if zona == "rural" else random.uniform(15, 80), 1),
                "poblacion":            None,
                "zona":                 zona,
                "sector":               "tecnologia",
                "fuente":               "DANE-MinTIC-SIMULADO",
            })

    logger.info(f"Datos sinteticos de conectividad generados: {len(registros)} registros")
    return registros


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    datos = extraer_conectividad()
    print(f"Total registros: {len(datos)}")
    if datos:
        print("Primeros 3:")
        for d in datos[:3]:
            print(" ", d)
