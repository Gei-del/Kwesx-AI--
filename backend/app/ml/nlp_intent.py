"""
backend/app/ml/nlp_intent.py
==============================
Clasificador de intención basado en TF-IDF + similitud coseno.

Reemplaza el motor keyword-based de asistente.py v1 por un enfoque
vectorial que es más robusto a variaciones en el lenguaje natural.

Características
---------------
- Sin dependencia de modelos externos (solo scikit-learn)
- Corpus de entrenamiento en español colombiano territorial
- Fallback a keyword-based si sklearn no está instalado
- Devuelve intención + score de confianza

Uso
---
from backend.app.ml.nlp_intent import clasificar_intencion

intencion, confianza = clasificar_intencion("¿Va a llover esta semana?")
# → ("clima", 0.87)
"""

from __future__ import annotations
import re
import unicodedata
from typing import NamedTuple

# ─── Corpus de entrenamiento ─────────────────────────────────────────────────
#
# Frases representativas por intención en español colombiano.
# Más frases = mejor generalización. Agregar frases aquí es suficiente
# para mejorar el clasificador sin reentrenar ningún modelo externo.
#
# Intenciones disponibles:
#   trafico   — peajes, vehículos, ANI, carreteras
#   precios   — insumos agrícolas, fertilizantes, UPRA, costos campo
#   clima     — lluvia, temperatura, IDEAM, alertas climáticas
#   resumen   — cuántos datos, estado del sistema, MTU
#   ayuda     — qué puedes hacer, cómo funciona
#   ivt       — vulnerabilidad territorial, predicción, índice IVT
#   anomalia  — alertas, anomalías, algo raro, alertas
#   forecast  — predicción futura, próximos meses, tendencia
# ─────────────────────────────────────────────────────────────────────────────

CORPUS: list[tuple[str, str]] = [
    # ── Tráfico / ANI ──────────────────────────────────────────────────────
    ("cuántos vehículos pasaron por los peajes de antioquia", "trafico"),
    ("tráfico vehicular en las carreteras colombianas", "trafico"),
    ("cuántos carros pasaron por el peaje el vino", "trafico"),
    ("índice de evasión en peajes nacionales", "trafico"),
    ("flujo de tránsito en la vía panamericana", "trafico"),
    ("peajes con más tráfico en colombia", "trafico"),
    ("evasores en los peajes del valle del cauca", "trafico"),
    ("cuánto tráfico hay en la autopista bogotá medellín", "trafico"),
    ("datos de transito en la red vial primaria", "trafico"),
    ("categorías de vehículos que pasan por los peajes", "trafico"),
    ("estado de las vías nacionales", "trafico"),
    ("cierres en las carreteras del país", "trafico"),
    ("información de peajes en colombia", "trafico"),
    ("ani datos de tráfico", "trafico"),
    ("cuántos camiones pasan por santander", "trafico"),
    ("tarifa peaje camiones vía al llano", "trafico"),
    ("hay trancón en la vía a cali", "trafico"),

    # ── Precios / UPRA ─────────────────────────────────────────────────────
    ("cómo están los precios de insumos agrícolas", "precios"),
    ("han subido los fertilizantes este año", "precios"),
    ("cuánto cuestan los plaguicidas en colombia", "precios"),
    ("índice de precios de insumos upra", "precios"),
    ("tendencia del precio de herbicidas y fungicidas", "precios"),
    ("costo de semillas certificadas en el mercado", "precios"),
    ("precio de los insumos para el campo", "precios"),
    ("cuánto ha variado el precio de fertilizantes", "precios"),
    ("subida de precios agrícolas 2026", "precios"),
    ("cómo está el índice upra este mes", "precios"),
    ("cuánto cuesta el urea en colombia", "precios"),
    ("precio del glifosato y herbicidas agrícolas", "precios"),
    ("información de costos para agricultores", "precios"),
    ("variación mensual del precio de insumos", "precios"),
    ("cuánto han subido los plaguicidas desde enero", "precios"),

    # ── Clima / IDEAM ──────────────────────────────────────────────────────
    ("cuánta lluvia cayó en medellín esta semana", "clima"),
    ("temperatura promedio en bogotá hoy", "clima"),
    ("precipitación en el caribe colombiano este mes", "clima"),
    ("hay alerta climática en el pacífico", "clima"),
    ("ideam datos de temperatura y lluvia", "clima"),
    ("cuál es la zona más lluviosa de colombia", "clima"),
    ("estaciones meteorológicas del ideam", "clima"),
    ("cómo está el clima en el amazonas", "clima"),
    ("fenómeno el niño y la niña en colombia", "clima"),
    ("anomalía de temperatura en la región andina", "clima"),
    ("va a llover mañana en cundinamarca", "clima"),
    ("cuántos milímetros de lluvia registró barranquilla", "clima"),
    ("cuál fue la temperatura máxima en cali", "clima"),
    ("hay sequía en la costa atlántica", "clima"),
    ("alerta naranja por lluvias en el chocó", "clima"),
    ("cómo está el tiempo en colombia hoy", "clima"),
    ("pronóstico de lluvia para el eje cafetero", "clima"),
    ("humedad relativa en cartagena", "clima"),

    # ── Resumen / Estado MTU ───────────────────────────────────────────────
    ("cuántos registros tiene el sistema", "resumen"),
    ("qué datos hay disponibles en kwesx ai", "resumen"),
    ("estado actual del modelo territorial", "resumen"),
    ("cuántos datos tiene el mtu", "resumen"),
    ("resumen de información disponible", "resumen"),
    ("cuántas fuentes de datos están activas", "resumen"),
    ("qué tan actualizada está la información", "resumen"),
    ("cuántos datos de ani upra e ideam hay", "resumen"),
    ("cuántos registros tiene la base de datos", "resumen"),
    ("dame un resumen del estado del sistema", "resumen"),

    # ── Ayuda / Capacidades ────────────────────────────────────────────────
    ("qué puedes hacer", "ayuda"),
    ("cómo funciona kwesx ai", "ayuda"),
    ("ayúdame a entender esta aplicación", "ayuda"),
    ("qué tipo de preguntas puedo hacerte", "ayuda"),
    ("cuáles son tus capacidades", "ayuda"),
    ("para qué sirve este asistente", "ayuda"),
    ("dame un ejemplo de lo que puedo preguntar", "ayuda"),
    ("explícame cómo usar kwesx", "ayuda"),
    ("qué temas cubre el asistente", "ayuda"),
    ("qué datos puedo consultar aquí", "ayuda"),

    # ── IVT / Vulnerabilidad ───────────────────────────────────────────────
    ("cuál es el índice de vulnerabilidad territorial", "ivt"),
    ("cómo está la vulnerabilidad en mi zona", "ivt"),
    ("predicción del ivt para este mes", "ivt"),
    ("qué tan vulnerable es mi territorio", "ivt"),
    ("resultado del modelo de predicción territorial", "ivt"),
    ("cuál es la calidad de vida en mi municipio", "ivt"),
    ("índice territorial actual", "ivt"),
    ("cómo clasificó el modelo mi región", "ivt"),
    ("predicción de riesgo territorial", "ivt"),
    ("nivel de vulnerabilidad alto medio bajo", "ivt"),

    # ── Anomalías ──────────────────────────────────────────────────────────
    ("hay alguna anomalía en los datos", "anomalia"),
    ("qué alertas hay activas en el sistema", "anomalia"),
    ("detectaron algo raro en los datos climáticos", "anomalia"),
    ("outliers en los precios agrícolas", "anomalia"),
    ("datos atípicos en las mediciones del ideam", "anomalia"),
    ("hay valores extremos en el tráfico", "anomalia"),
    ("el sistema detectó alguna alerta", "anomalia"),
    ("qué anomalías reporta el modelo", "anomalia"),

    # ── Forecasting / Predicción futura ────────────────────────────────────
    ("cómo van a estar los precios el próximo mes", "forecast"),
    ("predicción de lluvia para los próximos 3 meses", "forecast"),
    ("tendencia futura del tráfico en colombia", "forecast"),
    ("proyección de precios de insumos para 2026", "forecast"),
    ("cuál es el pronóstico del índice upra", "forecast"),
    ("qué va a pasar con el clima en los próximos meses", "forecast"),
    ("predicción de series temporales", "forecast"),
    ("forecast de precipitación para el segundo semestre", "forecast"),
    ("tendencia esperada del flujo vehicular", "forecast"),
    ("cuánto van a subir los fertilizantes", "forecast"),
]

# ─── Normalización ────────────────────────────────────────────────────────────

def _normalizar(texto: str) -> str:
    """Minúsculas, sin acentos, sin puntuación."""
    texto = texto.lower().strip()
    # Eliminar acentos preservando ñ
    nfkd = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in nfkd if not unicodedata.combining(c) or c == "ñ")
    # Eliminar puntuación
    texto = re.sub(r"[^\w\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


# ─── Clasificador ─────────────────────────────────────────────────────────────

class IntentResult(NamedTuple):
    intencion: str
    confianza: float


# Intentamos construir el vectorizador TF-IDF al importar el módulo.
# Si sklearn no está disponible, fallback a keyword-based.
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    _frases    = [_normalizar(f) for f, _ in CORPUS]
    _etiquetas = [e for _, e in CORPUS]

    _vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),       # unigramas + bigramas
        min_df=1,
        sublinear_tf=True,
    )
    _tfidf_matrix = _vectorizer.fit_transform(_frases)

    _NLP_DISPONIBLE = True

except ImportError:
    _NLP_DISPONIBLE = False


def _keyword_fallback(texto: str) -> IntentResult:
    """Fallback keyword-based si sklearn no está disponible."""
    KEYWORDS = {
        "trafico":  ["trafico", "peaje", "vehiculo", "transito", "carretera", "ani"],
        "precios":  ["precio", "insumo", "fertilizante", "plaguicida", "upra", "agricola"],
        "clima":    ["lluvia", "precipitacion", "temperatura", "clima", "ideam", "sequia"],
        "resumen":  ["resumen", "estado", "cuantos", "registros", "mtu"],
        "ayuda":    ["ayuda", "puedes", "funciona", "ejemplo", "capacidades"],
        "ivt":      ["vulnerabilidad", "ivt", "territorial", "prediccion", "riesgo"],
        "anomalia": ["anomalia", "alerta", "raro", "atipico", "outlier"],
        "forecast": ["proximo", "futuro", "tendencia", "proyeccion", "forecast"],
    }
    texto_n = _normalizar(texto)
    scores = {k: sum(1 for w in kws if w in texto_n) for k, kws in KEYWORDS.items()}
    mejor = max(scores, key=scores.get)
    if scores[mejor] == 0:
        return IntentResult("desconocido", 0.0)
    total = sum(scores.values())
    return IntentResult(mejor, round(scores[mejor] / total, 2))


def clasificar_intencion(texto: str) -> IntentResult:
    """
    Clasifica la intención de un texto en lenguaje natural.

    Retorna IntentResult(intencion, confianza) donde confianza ∈ [0, 1].

    Usa TF-IDF + coseno si sklearn está disponible,
    keyword-based como fallback si no.
    """
    if not texto or not texto.strip():
        return IntentResult("desconocido", 0.0)

    if not _NLP_DISPONIBLE:
        return _keyword_fallback(texto)

    texto_n = _normalizar(texto)
    vec = _vectorizer.transform([texto_n])
    sims = cosine_similarity(vec, _tfidf_matrix)[0]

    top_idx = int(np.argmax(sims))
    top_score = float(sims[top_idx])

    if top_score < 0.05:
        return IntentResult("desconocido", round(top_score, 3))

    # Sumar scores por intención y elegir la mejor
    scores_por_intencion: dict[str, float] = {}
    for idx, score in enumerate(sims):
        intent = _etiquetas[idx]
        scores_por_intencion[intent] = max(scores_por_intencion.get(intent, 0.0), float(score))

    mejor_intent = max(scores_por_intencion, key=scores_por_intencion.get)
    confianza = round(scores_por_intencion[mejor_intent], 3)

    return IntentResult(mejor_intent, confianza)
