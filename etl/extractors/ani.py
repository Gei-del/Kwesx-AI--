"""
etl/extractors/ani.py
=====================
Extractor para el dataset ANI — Tráfico Vehicular en Peajes de Colombia.

Dataset: https://www.datos.gov.co/d/8yi9-t44c
ID Socrata: 8yi9-t44c
Registros: ~151,453 (confirmado 2026-06-30)
Frecuencia: no se actualiza regularmente

Columnas del dataset original
------------------------------
idpeaje            — código único del peaje
peaje              — nombre del peaje
categoriatarifa    — categoría vehicular (I, II, III...)
desde              — fecha inicio del período (YYYY-MM-DD)
hasta              — fecha fin del período (YYYY-MM-DD)
valortarifa        — valor del peaje en COP
cantidadtrafico    — vehículos que pagaron
cantidadevasores   — vehículos que evadieron
cantidadexentos787 — vehículos exentos (decreto 787)

Nota geográfica
---------------
El dataset ANI NO incluye lat/lon ni código DANE directamente.
La ubicación de los peajes se resuelve con el diccionario PEAJES_DANE
definido abajo (los ~30 peajes más importantes de la red vial nacional).
Para peajes no mapeados, codigo_dane y coordenadas quedan en NULL.
"""

from .base import SocrataExtractor
from etl.config import ANI_DATASET_ID

# ─────────────────────────────────────────────────────────────────────────────
# Lookup manual: nombre del peaje → (codigo_dane, departamento, municipio,
#                                     latitud, longitud)
# Fuente: ANI — Corredores Concesionados + DIVIPOLA 2024
# Se puede ampliar con más peajes conforme avance el proyecto.
# ─────────────────────────────────────────────────────────────────────────────
PEAJES_DANE: dict[str, tuple] = {
    # nombre_peaje_lower: (dane, dpto, mun, lat, lon)
    "la ye":            ("05001", "Antioquia", "Medellín",        6.2518, -75.5636),
    "marinilla":        ("05440", "Antioquia", "Marinilla",       6.1763, -75.3331),
    "santuario":        ("05736", "Antioquia", "Santuario",       6.1397, -75.2715),
    "el higado":        ("05088", "Antioquia", "Bello",           6.3397, -75.5560),
    "hatillo":          ("05088", "Antioquia", "Bello",           6.3900, -75.5630),
    "tribunas":         ("66001", "Risaralda", "Pereira",         4.7967, -75.6942),
    "la paila":         ("76233", "Valle del Cauca", "Dagua",     3.7186, -76.3936),
    "boquía":           ("63001", "Quindío", "Armenia",           4.5339, -75.6810),
    "cruces":           ("17001", "Caldas", "Manizales",          5.0703, -75.5136),
    "alto de las palmas":("05001","Antioquia", "Medellín",        6.2000, -75.4800),
    "chimichagua":      ("20238", "Cesar", "Chimichagua",         9.2547, -73.8175),
    "siberia":          ("25754", "Cundinamarca", "Tenjo",        4.8697, -74.1878),
    "chia":             ("25175", "Cundinamarca", "Chía",         4.8620, -74.0588),
    "tobia grande":     ("25658", "Cundinamarca", "Quebradanegra",5.0614, -74.4606),
    "la virgen":        ("25126", "Cundinamarca", "Cajicá",       4.9267, -74.0264),
    "corredor norte":   ("11001", "Bogotá D.C.", "Bogotá",        4.6097, -74.0817),
    "fontibón":         ("11001", "Bogotá D.C.", "Bogotá",        4.6926, -74.1469),
    "zipaquirá":        ("25899", "Cundinamarca", "Zipaquirá",    5.0228, -74.0077),
    "briceño":          ("05107", "Antioquia", "Briceño",         7.0967, -75.5261),
    "río grande":       ("05001", "Antioquia", "Medellín",        6.5500, -75.6000),
    "puerto araujo":    ("13300", "Bolívar", "Hatillo de Loba",   8.9594, -74.0669),
    "turbana":          ("13780", "Bolívar", "Turbana",           10.3000, -75.3833),
    "ciénaga":          ("47189", "Magdalena", "Ciénaga",         11.0048, -74.2507),
    "sevilla":          ("47660", "Magdalena", "Sevilla",         10.5683, -74.1131),
    "bosconia":         ("20060", "Cesar", "Bosconia",            9.9756, -73.8939),
    "la pintada":       ("05541", "Antioquia", "La Pintada",      5.7514, -75.5994),
    "amagá":            ("05030", "Antioquia", "Amagá",           6.0367, -75.7028),
    "barbosa":          ("05079", "Antioquia", "Barbosa",         6.4367, -75.3319),
    "la miel":          ("17174", "Caldas", "Samaná",             5.6047, -74.9261),
    "km 18 buenaventura":("76113","Valle del Cauca","Buenaventura",3.8878,-76.9200),
}


class ANIExtractor(SocrataExtractor):
    """
    Extractor específico para el dataset ANI de tráfico en peajes.

    Uso
    ---
    from etl.extractors.ani import ANIExtractor

    ext = ANIExtractor()
    registros = ext.fetch_all()          # todos los datos
    registros = ext.fetch_from("2023-01-01")  # desde una fecha
    """

    def __init__(self):
        super().__init__(
            dataset_id=ANI_DATASET_ID,
            nombre="ANI Tráfico Peajes",
        )

    def fetch_all_raw(self) -> list[dict]:
        """
        Descarga todos los registros sin filtro.
        (~151,453 filas — puede tardar ~2 min dependiendo del ancho de banda)
        """
        return self.fetch_all(order="desde")

    def fetch_from(self, fecha_inicio: str) -> list[dict]:
        """
        Descarga registros donde el período empieza en o después de fecha_inicio.
        fecha_inicio: str en formato 'YYYY-MM-DD'
        """
        return self.fetch_all(
            where=f"desde >= '{fecha_inicio}'",
            order="desde",
        )

    def enrich_with_location(self, registros: list[dict]) -> list[dict]:
        """
        Agrega codigo_dane, departamento, municipio, latitud y longitud
        a cada registro usando el diccionario PEAJES_DANE.

        Peajes no mapeados reciben NULL en esos campos.
        """
        for r in registros:
            nombre_peaje = (r.get("peaje") or "").strip().lower()
            geo = PEAJES_DANE.get(nombre_peaje)
            if geo:
                r["codigo_dane"], r["departamento"], r["municipio"], \
                    r["latitud"], r["longitud"] = geo
            else:
                r["codigo_dane"] = None
                r["departamento"] = None
                r["municipio"] = None
                r["latitud"] = None
                r["longitud"] = None
        return registros
