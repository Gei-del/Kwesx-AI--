"""
etl/loaders/postgres.py
========================
Loader para insertar registros normalizados en PostgreSQL.

Usa SQLAlchemy Core (no ORM) para inserciones en bulk — más eficiente
cuando se cargan miles de registros de una vez.

Las tablas se crean si no existen, usando los modelos definidos en
backend/app/models/mtu.py. Si la tabla ya tiene datos, la inserción
es incremental (INSERT ... ON CONFLICT DO NOTHING).
"""

from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from loguru import logger

from etl.config import DATABASE_URL_SYNC
from backend.app.models.mtu import Base, MtuANI, MtuUPRA, MtuIDEAM, MtuConectividad, MtuEducacion


class PostgresLoader:
    """
    Loader que guarda registros MTU en PostgreSQL.

    Uso
    ---
    from etl.loaders.postgres import PostgresLoader

    loader = PostgresLoader()
    loader.create_tables()            # crea tablas si no existen
    loader.load_ani(registros_norm)   # inserta datos ANI
    loader.load_upra(registros_norm)  # inserta datos UPRA
    loader.load_ideam(registros_norm) # inserta datos IDEAM
    """

    def __init__(self, database_url: str = DATABASE_URL_SYNC):
        self.engine = create_engine(database_url, echo=False)
        logger.info(f"[Loader] Conectado a: {database_url.split('@')[-1]}")

    def create_tables(self) -> None:
        """
        Crea todas las tablas del MTU si no existen.
        Seguro de ejecutar múltiples veces (checkfirst=True).
        """
        Base.metadata.create_all(self.engine, checkfirst=True)
        logger.success("[Loader] Tablas MTU verificadas/creadas.")

    def load_ani(self, registros: list[dict]) -> int:
        """
        Inserta registros ANI normalizados.
        Retorna el número de filas insertadas.
        """
        return self._bulk_insert(MtuANI, registros, conflict_cols=["idpeaje", "fecha_inicio", "categoria_tarifa"])

    def load_upra(self, registros: list[dict]) -> int:
        """
        Inserta registros UPRA normalizados.
        Retorna el número de filas insertadas.
        """
        return self._bulk_insert(MtuUPRA, registros, conflict_cols=["fecha"])

    def load_ideam(self, registros: list[dict]) -> int:
        """
        Inserta registros IDEAM normalizados (precipitación + temperatura).
        Retorna el número de filas insertadas.
        """
        return self._bulk_insert(
            MtuIDEAM, registros,
            conflict_cols=["codigo_estacion", "codigo_sensor", "fecha"],
        )

    def load_conectividad(self, registros: list[dict]) -> int:
        """
        Inserta registros de conectividad (DANE + MinTIC).
        Conflict key: codigo_dane + anio + tipo_conexion + zona.
        """
        return self._bulk_insert(
            MtuConectividad, registros,
            conflict_cols=["codigo_dane", "anio", "tipo_conexion", "zona"],
        )

    def load_educacion(self, registros: list[dict]) -> int:
        """
        Inserta registros de cobertura educativa (MEN-SIMAT).
        Conflict key: codigo_dane + anio + nivel_educativo + zona.
        """
        return self._bulk_insert(
            MtuEducacion, registros,
            conflict_cols=["codigo_dane", "anio", "nivel_educativo", "zona"],
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Método interno
    # ──────────────────────────────────────────────────────────────────────────

    def _bulk_insert(
        self,
        model,
        registros: list[dict],
        conflict_cols: list[str],
        chunk_size: int = 1000,
    ) -> int:
        """
        Inserta registros en bulk usando INSERT ... ON CONFLICT DO NOTHING.

        Divide los datos en chunks de `chunk_size` para no saturar
        la memoria ni generar queries demasiado grandes.

        conflict_cols: columnas que forman la restricción UNIQUE
        """
        if not registros:
            logger.warning(f"[Loader] Sin registros para insertar en {model.__tablename__}.")
            return 0

        tabla = model.__tablename__
        total_insertados = 0

        with self.engine.begin() as conn:
            for i in range(0, len(registros), chunk_size):
                chunk = registros[i : i + chunk_size]

                stmt = pg_insert(model).values(chunk)
                stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols)

                result = conn.execute(stmt)
                insertados = result.rowcount
                total_insertados += insertados

                logger.debug(
                    f"[Loader] {tabla}: chunk {i // chunk_size + 1} → "
                    f"{insertados}/{len(chunk)} filas insertadas."
                )

        logger.success(
            f"[Loader] {tabla}: {total_insertados}/{len(registros)} "
            f"registros insertados (duplicados omitidos)."
        )
        return total_insertados

    def query(self, sql: str) -> list[dict]:
        """Ejecuta una query SQL libre y retorna lista de dicts. Para validación."""
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result]
