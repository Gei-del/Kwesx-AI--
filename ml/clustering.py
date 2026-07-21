"""
ml/clustering.py
================
Segmentación territorial no supervisada para Kwesx AI.

Algoritmos
----------
1. KMeans — Agrupa municipios/períodos por perfil territorial similar.
   Genera N perfiles (default 4) con etiquetas semánticas automáticas.

2. DBSCAN — Detecta clústeres de densidad variable y outliers.
   Útil para encontrar agrupaciones irregulares sin asumir forma esférica.

Aplicaciones
------------
- Segmentar departamentos/municipios por perfil de riesgo agrícola
- Identificar grupos de períodos con comportamiento climático similar
- Detectar anomalías geográficas (períodos/zonas sin patrón)
- Base para el motor de recomendaciones y el mapa de calor territorial

Uso
---
    from ml.clustering import ClusterizadorTerritorial
    modelo = ClusterizadorTerritorial(n_clusters=4)
    resultado = modelo.fit_predict(df_features)
    modelo.save()

    # Para segmentar nuevos puntos:
    clusters = modelo.predict(df_nuevos)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from ml.features import FEATURE_COLS

# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

MODEL_DIR       = Path(__file__).parent / "models"
CLUSTER_PATH    = MODEL_DIR / "clustering.pkl"
CLUSTER_META    = MODEL_DIR / "clustering_metadata.json"

# Features relevantes para clusterización territorial
# (excluimos las temporales puras — mes/año — que no describen el perfil)
CLUSTER_FEATURES = [
    "upra_indice_total",
    "upra_var_mensual_pct",
    "upra_fertilizantes",
    "upra_plaguicidas",
    "ideam_precipitacion_mm",
    "ideam_precipitacion_anomalia",
    "ideam_temperatura_c",
    "ideam_temperatura_anomalia",
]

# Nombres semánticos de los 4 perfiles (se asignan post-hoc por centroides)
PERFIL_NOMBRES = {
    "precio_alto_sequia":     "🔴 Alto riesgo: precios altos + déficit hídrico",
    "precio_alto_lluvia":     "🟠 Riesgo moderado-alto: precios altos + lluvias",
    "precio_bajo_normal":     "🟡 Riesgo moderado: precios estables + clima normal",
    "precio_bajo_exceso":     "🟢 Bajo riesgo: precios bajos + buenas condiciones",
}


# ─────────────────────────────────────────────────────────────────────────────
# Clase principal
# ─────────────────────────────────────────────────────────────────────────────

class ClusterizadorTerritorial:
    """
    Segmentación territorial no supervisada.

    Combina KMeans (clústeres compactos) con DBSCAN (densidad + outliers)
    para obtener una visión completa del paisaje territorial.
    """

    def __init__(self, n_clusters: int = 4):
        self.n_clusters = n_clusters
        self.kmeans: KMeans | None = None
        self.dbscan: DBSCAN | None = None
        self.scaler: StandardScaler | None = None
        self.centroides_df: pd.DataFrame | None = None
        self.metadata: dict[str, Any] = {}
        self.perfiles: dict[int, dict[str, Any]] = {}

    # ── Búsqueda del K óptimo ─────────────────────────────────────────────────

    def _find_optimal_k(self, X_scaled: np.ndarray, k_range: range = range(2, 8)) -> int:
        """
        Usa el coeficiente de silhouette para encontrar el K óptimo.
        Si los datos son pocos, limita el rango a evitar K >= n_samples.
        """
        max_k = min(max(k_range), len(X_scaled) // 3)
        if max_k < 2:
            return 2

        best_k, best_score = 2, -1.0
        for k in range(2, max_k + 1):
            km = KMeans(n_clusters=k, random_state=2026, n_init=10)
            labels = km.fit_predict(X_scaled)
            try:
                score = silhouette_score(X_scaled, labels)
                if score > best_score:
                    best_score, best_k = score, k
            except ValueError:
                continue

        logger.info(f"[Clustering] K óptimo: {best_k} (silhouette={best_score:.4f})")
        return best_k

    # ── Entrenamiento / fit ───────────────────────────────────────────────────

    def fit_predict(
        self,
        df: pd.DataFrame,
        auto_k: bool = True,
        dbscan_eps: float = 0.8,
        dbscan_min_samples: int = 3,
    ) -> pd.DataFrame:
        """
        Entrena KMeans y DBSCAN y añade columnas de cluster al DataFrame.

        Parámetros
        ----------
        df : DataFrame con al menos las columnas de CLUSTER_FEATURES
        auto_k : Si True, busca el K óptimo; si False, usa self.n_clusters
        dbscan_eps : Epsilon de DBSCAN (radio de vecindad en espacio normalizado)
        dbscan_min_samples : Mínimo de puntos para formar un núcleo DBSCAN

        Retorna
        -------
        DataFrame con columnas adicionales:
          - cluster_kmeans : ID de clúster KMeans (0..K-1)
          - cluster_kmeans_label : Etiqueta semántica del clúster
          - cluster_dbscan : ID de clúster DBSCAN (-1 = outlier)
          - es_outlier : bool, True si DBSCAN clasificó como ruido
        """
        if len(df) < 6:
            raise ValueError(f"Se necesitan al menos 6 filas para clustering: {len(df)} recibidas.")

        # Seleccionar y limpiar features
        cols_disponibles = [c for c in CLUSTER_FEATURES if c in df.columns]
        X = df[cols_disponibles].fillna(0.0)

        # Normalizar
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # ── KMeans ───────────────────────────────────────────────────────────
        if auto_k:
            self.n_clusters = self._find_optimal_k(X_scaled)

        self.kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=2026,
            n_init=20,
            max_iter=500,
        )
        kmeans_labels = self.kmeans.fit_predict(X_scaled)

        # ── DBSCAN ───────────────────────────────────────────────────────────
        self.dbscan = DBSCAN(
            eps=dbscan_eps,
            min_samples=min(dbscan_min_samples, len(df) // 3 + 1),
            metric="euclidean",
            n_jobs=-1,
        )
        dbscan_labels = self.dbscan.fit_predict(X_scaled)

        # ── Métricas de calidad ───────────────────────────────────────────────
        metricas_kmeans: dict[str, float] = {}
        if len(set(kmeans_labels)) > 1:
            try:
                metricas_kmeans["silhouette"]        = round(float(silhouette_score(X_scaled, kmeans_labels)), 4)
                metricas_kmeans["davies_bouldin"]    = round(float(davies_bouldin_score(X_scaled, kmeans_labels)), 4)
                metricas_kmeans["calinski_harabasz"] = round(float(calinski_harabasz_score(X_scaled, kmeans_labels)), 4)
            except Exception:
                pass

        # ── Perfiles semánticos ───────────────────────────────────────────────
        self._generar_perfiles(df, cols_disponibles, kmeans_labels)

        # ── Agregar al DataFrame ──────────────────────────────────────────────
        df_out = df.copy()
        df_out["cluster_kmeans"]       = kmeans_labels
        df_out["cluster_kmeans_label"] = [self.perfiles.get(c, {}).get("nombre", f"Perfil {c}") for c in kmeans_labels]
        df_out["cluster_dbscan"]       = dbscan_labels
        df_out["es_outlier"]           = dbscan_labels == -1

        # ── Metadatos ────────────────────────────────────────────────────────
        n_outliers = int((dbscan_labels == -1).sum())
        n_dbscan_clusters = len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)

        self.metadata = {
            "n_samples":              len(df),
            "features_usadas":        cols_disponibles,
            "kmeans": {
                "n_clusters":         self.n_clusters,
                "inercia":            round(float(self.kmeans.inertia_), 4),
                **metricas_kmeans,
            },
            "dbscan": {
                "eps":                dbscan_eps,
                "min_samples":        dbscan_min_samples,
                "n_clusters":         n_dbscan_clusters,
                "n_outliers":         n_outliers,
                "pct_outliers":       round(n_outliers / len(df) * 100, 2),
            },
            "perfiles":               {str(k): v for k, v in self.perfiles.items()},
            "entrenado_en":           datetime.now().isoformat(),
        }

        logger.success(
            f"[Clustering] OK. KMeans: {self.n_clusters} clústeres "
            f"(silhouette={metricas_kmeans.get('silhouette', '?')}) | "
            f"DBSCAN: {n_dbscan_clusters} clústeres + {n_outliers} outliers"
        )
        return df_out

    def _generar_perfiles(
        self,
        df: pd.DataFrame,
        cols: list[str],
        labels: np.ndarray,
    ) -> None:
        """
        Genera etiquetas semánticas para cada clúster basándose en
        los valores medianos de sus centroides.
        """
        self.perfiles = {}
        df_c = df[cols].copy()
        df_c["_cluster"] = labels

        for cluster_id in sorted(set(labels)):
            grupo = df_c[df_c["_cluster"] == cluster_id]
            medianas = grupo.drop("_cluster", axis=1).median()

            # Determinar etiqueta semántica por reglas de dominio
            precio_alto = (
                "upra_indice_total" in medianas and
                medianas["upra_indice_total"] > df_c["upra_indice_total"].quantile(0.6)
                if "upra_indice_total" in df_c.columns else False
            )
            sequia = (
                "ideam_precipitacion_anomalia" in medianas and
                medianas["ideam_precipitacion_anomalia"] < -20
            )
            exceso_lluvia = (
                "ideam_precipitacion_anomalia" in medianas and
                medianas["ideam_precipitacion_anomalia"] > 20
            )

            if precio_alto and sequia:
                nombre = "🔴 Riesgo alto: precios altos + déficit hídrico"
                riesgo = "ALTA"
            elif precio_alto:
                nombre = "🟠 Riesgo moderado-alto: presión de precios"
                riesgo = "MEDIA-ALTA"
            elif exceso_lluvia:
                nombre = "🟡 Atención: exceso hídrico"
                riesgo = "MEDIA"
            else:
                nombre = "🟢 Condiciones favorables"
                riesgo = "BAJA"

            self.perfiles[int(cluster_id)] = {
                "cluster_id": int(cluster_id),
                "nombre":     nombre,
                "riesgo":     riesgo,
                "n_periodos": int(len(grupo)),
                "medianas":   {k: round(float(v), 3) for k, v in medianas.items()},
            }

    # ── Predicción para nuevos datos ──────────────────────────────────────────

    def predict(self, df_nuevo: pd.DataFrame) -> pd.DataFrame:
        """Asigna clúster KMeans a nuevas observaciones."""
        if self.kmeans is None or self.scaler is None:
            raise RuntimeError("Modelo no entrenado. Ejecuta fit_predict() primero.")

        cols = [c for c in CLUSTER_FEATURES if c in df_nuevo.columns]
        X = df_nuevo[cols].fillna(0.0)
        X_scaled = self.scaler.transform(X)
        clusters = self.kmeans.predict(X_scaled)

        df_out = df_nuevo.copy()
        df_out["cluster_kmeans"]       = clusters
        df_out["cluster_kmeans_label"] = [
            self.perfiles.get(int(c), {}).get("nombre", f"Perfil {c}") for c in clusters
        ]
        return df_out

    # ── Resumen para API ──────────────────────────────────────────────────────

    def get_resumen_api(self) -> dict[str, Any]:
        """Devuelve un resumen serializable para el endpoint /ml/clustering."""
        return {
            "modelo":   "ClusterizadorTerritorial (KMeans + DBSCAN)",
            "metadata": self.metadata,
            "perfiles": {str(k): v for k, v in self.perfiles.items()},
        }

    # ── Persistencia ──────────────────────────────────────────────────────────

    def save(self) -> str:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "kmeans":   self.kmeans,
            "dbscan":   self.dbscan,
            "scaler":   self.scaler,
            "perfiles": self.perfiles,
            "metadata": self.metadata,
        }, CLUSTER_PATH)
        with open(CLUSTER_META, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        logger.success(f"[Clustering] Guardado en {CLUSTER_PATH}")
        return str(CLUSTER_PATH)

    def load(self) -> "ClusterizadorTerritorial":
        if not CLUSTER_PATH.exists():
            raise FileNotFoundError(f"Modelo no encontrado en {CLUSTER_PATH}.")
        data = joblib.load(CLUSTER_PATH)
        self.kmeans   = data["kmeans"]
        self.dbscan   = data["dbscan"]
        self.scaler   = data["scaler"]
        self.perfiles = data.get("perfiles", {})
        self.metadata = data.get("metadata", {})
        logger.info(f"[Clustering] Cargado desde {CLUSTER_PATH}")
        return self

    def is_trained(self) -> bool:
        return CLUSTER_PATH.exists()
