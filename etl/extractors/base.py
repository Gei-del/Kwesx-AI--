"""
etl/extractors/base.py
======================
Clase base para todos los extractores de datos de Kwesx AI.

Encapsula la lógica de llamadas a la API Socrata de datos.gov.co:
- Paginación automática con $offset y $limit
- Reintentos con backoff exponencial
- Logging consistente
- Retorna siempre una lista de dicts (registros crudos JSON)

Los extractores específicos (ani.py, upra.py, ideam.py) heredan de esta
clase e implementan solo la lógica particular de su dataset.
"""

import time
import requests
from loguru import logger
from etl.config import SOCRATA_BASE, SOCRATA_HEADERS, BATCH_SIZE


class SocrataExtractor:
    """
    Extractor genérico para cualquier dataset de datos.gov.co (Socrata).

    Parámetros
    ----------
    dataset_id : str
        El identificador único del dataset en Socrata (p. ej. '8yi9-t44c').
    nombre : str
        Nombre legible del dataset para el logging.
    """

    def __init__(self, dataset_id: str, nombre: str):
        self.dataset_id = dataset_id
        self.nombre = nombre
        self.url = f"{SOCRATA_BASE}/{dataset_id}.json"

    def fetch_all(
        self,
        where: str = "",
        select: str = "",
        order: str = "",
        limit: int = None,
    ) -> list[dict]:
        """
        Descarga todos los registros del dataset usando paginación.

        Parámetros
        ----------
        where  : filtro SoQL (p. ej. "fecha >= '2024-01-01'")
        select : columnas a traer (p. ej. "fecha, valorobservado")
        order  : columna de orden para paginación estable
        limit  : máximo total de registros (None = todos)

        Retorna
        -------
        list[dict] — lista de registros en formato JSON crudo
        """
        all_records: list[dict] = []
        offset = 0
        batch = BATCH_SIZE

        logger.info(f"[{self.nombre}] Iniciando extracción desde {self.url}")

        while True:
            params: dict = {"$limit": batch, "$offset": offset}
            if where:
                params["$where"] = where
            if select:
                params["$select"] = select
            if order:
                params["$order"] = order

            data = self._get_with_retry(params)

            if not data:
                break  # sin más datos

            all_records.extend(data)
            logger.info(
                f"[{self.nombre}] Página {offset // batch + 1}: "
                f"{len(data)} registros | Total acumulado: {len(all_records)}"
            )

            # Si limit está definido y ya lo alcanzamos, parar
            if limit and len(all_records) >= limit:
                all_records = all_records[:limit]
                break

            # Si la respuesta fue menor que el batch size, ya llegamos al final
            if len(data) < batch:
                break

            offset += batch

        logger.success(f"[{self.nombre}] Extracción completa: {len(all_records)} registros.")
        return all_records

    def count(self, where: str = "") -> int:
        """Retorna el conteo total de filas (útil para validación)."""
        params = {"$select": "count(*) AS total"}
        if where:
            params["$where"] = where
        data = self._get_with_retry(params)
        if data:
            return int(data[0].get("total", 0))
        return 0

    def sample(self, n: int = 3) -> list[dict]:
        """Retorna una muestra de n filas (útil para exploración)."""
        params = {"$limit": n}
        return self._get_with_retry(params) or []

    # ──────────────────────────────────────────────────────────────────────────
    # Métodos internos
    # ──────────────────────────────────────────────────────────────────────────

    def _get_with_retry(
        self, params: dict, max_retries: int = 3, backoff: float = 2.0
    ) -> list[dict]:
        """
        Hace GET a la API con reintentos y backoff exponencial.

        Si el servidor devuelve error 429 (rate limit) o 5xx,
        espera y reintenta automáticamente.
        """
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(
                    self.url,
                    headers=SOCRATA_HEADERS,
                    params=params,
                    timeout=60,
                )

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 429:
                    wait = backoff ** attempt
                    logger.warning(
                        f"[{self.nombre}] Rate limit (429). "
                        f"Reintento {attempt}/{max_retries} en {wait}s..."
                    )
                    time.sleep(wait)
                    continue

                logger.error(
                    f"[{self.nombre}] Error HTTP {response.status_code}: "
                    f"{response.text[:200]}"
                )

            except requests.exceptions.RequestException as exc:
                wait = backoff ** attempt
                logger.warning(
                    f"[{self.nombre}] Error de red: {exc}. "
                    f"Reintento {attempt}/{max_retries} en {wait}s..."
                )
                time.sleep(wait)

        logger.error(f"[{self.nombre}] Falló después de {max_retries} intentos.")
        return []
