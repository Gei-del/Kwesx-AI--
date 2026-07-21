"""
etl/pipeline.py
===============
Orquestador del pipeline ETL completo de Kwesx AI.

Coordina la secuencia Extracción → Transformación → Carga (ETL)
para los 3 datasets del MVP: ANI, UPRA e IDEAM.

Uso desde la terminal
---------------------
# Correr el pipeline completo (carga incremental por defecto)
python -m etl.pipeline

# Solo un dataset
python -m etl.pipeline --fuente ani
python -m etl.pipeline --fuente upra
python -m etl.pipeline --fuente ideam

# Especificar fecha de inicio
python -m etl.pipeline --fuente ideam --desde 2026-06-01

# Modo muestra (sin escribir en BD, solo imprime los primeros N registros)
python -m etl.pipeline --dry-run --fuente upra
"""

import argparse
import sys
from datetime import date
from loguru import logger

from etl.config import FECHA_INICIO, FECHA_FIN
from etl.extractors import ANIExtractor, UPRAExtractor, IDEAMExtractor
from etl.transformers import ANINormalizer, UPRANormalizer, IDEAMNormalizer
from etl.loaders.postgres import PostgresLoader
from backend.etl.extractors.dane_mintic import extraer_conectividad
from backend.etl.extractors.men import extraer_educacion


def run_ani(loader: PostgresLoader, desde: str, dry_run: bool = False) -> dict:
    """Ejecuta el pipeline ETL para ANI."""
    logger.info("=" * 60)
    logger.info("PIPELINE ANI — Tráfico Vehicular en Peajes")
    logger.info("=" * 60)

    # 1. Extracción
    extractor = ANIExtractor()
    registros_crudos = extractor.fetch_from(desde)

    # 2. Enriquecimiento geográfico
    registros_crudos = extractor.enrich_with_location(registros_crudos)

    # 3. Transformación (normalización al MTU)
    normalizador = ANINormalizer()
    registros_norm = normalizador.transform(registros_crudos)

    if dry_run:
        logger.info("[ANI] Modo dry-run: mostrando primeros 3 registros normalizados.")
        for r in registros_norm[:3]:
            logger.info(r)
        return {"fuente": "ANI", "extraidos": len(registros_crudos), "cargados": 0}

    # 4. Carga en PostgreSQL
    cargados = loader.load_ani(registros_norm)
    return {"fuente": "ANI", "extraidos": len(registros_crudos), "cargados": cargados}


def run_upra(loader: PostgresLoader, desde: str, dry_run: bool = False) -> dict:
    """Ejecuta el pipeline ETL para UPRA."""
    logger.info("=" * 60)
    logger.info("PIPELINE UPRA — Índice de Precios de Insumos Agrícolas")
    logger.info("=" * 60)

    # 1. Extracción
    extractor = UPRAExtractor()
    registros_crudos = extractor.fetch_from(desde)

    # 2. Transformación
    normalizador = UPRANormalizer()
    registros_norm = normalizador.transform(registros_crudos)

    if dry_run:
        logger.info("[UPRA] Modo dry-run: mostrando primeros 3 registros normalizados.")
        for r in registros_norm[:3]:
            logger.info(r)
        return {"fuente": "UPRA", "extraidos": len(registros_crudos), "cargados": 0}

    # 3. Carga
    cargados = loader.load_upra(registros_norm)
    return {"fuente": "UPRA", "extraidos": len(registros_crudos), "cargados": cargados}


def run_ideam(loader: PostgresLoader, dias: int = 30, dry_run: bool = False) -> dict:
    """
    Ejecuta el pipeline ETL para IDEAM.

    Por defecto carga los últimos `dias` días (default 30).
    Las tablas IDEAM son masivas — carga histórica completa es un proceso aparte.
    """
    logger.info("=" * 60)
    logger.info(f"PIPELINE IDEAM — Variables Climáticas (últimos {dias} días)")
    logger.info("=" * 60)

    # 1. Extracción
    extractor = IDEAMExtractor()
    registros_crudos = extractor.fetch_recent(dias=dias)

    # 2. Transformación
    normalizador = IDEAMNormalizer()
    registros_norm = normalizador.transform(registros_crudos)

    if dry_run:
        logger.info("[IDEAM] Modo dry-run: mostrando primeros 3 registros normalizados.")
        for r in registros_norm[:3]:
            logger.info(r)
        return {"fuente": "IDEAM", "extraidos": len(registros_crudos), "cargados": 0}

    # 3. Carga
    cargados = loader.load_ideam(registros_norm)
    return {"fuente": "IDEAM", "extraidos": len(registros_crudos), "cargados": cargados}


def run_conectividad(loader: PostgresLoader, dry_run: bool = False) -> dict:
    """Ejecuta el pipeline ETL para Conectividad (DANE + MinTIC)."""
    logger.info("=" * 60)
    logger.info("PIPELINE CONECTIVIDAD — Brecha Digital (DANE + MinTIC)")
    logger.info("=" * 60)

    registros = extraer_conectividad(app_token=None)

    if dry_run:
        logger.info("[Conectividad] Modo dry-run: mostrando primeros 2 registros.")
        for r in registros[:2]:
            logger.info(r)
        return {"fuente": "Conectividad", "extraidos": len(registros), "cargados": 0}

    cargados = loader.load_conectividad(registros)
    return {"fuente": "Conectividad", "extraidos": len(registros), "cargados": cargados}


def run_educacion(loader: PostgresLoader, dry_run: bool = False) -> dict:
    """Ejecuta el pipeline ETL para Educación (MEN-SIMAT)."""
    logger.info("=" * 60)
    logger.info("PIPELINE EDUCACION — Cobertura Escolar (MEN-SIMAT)")
    logger.info("=" * 60)

    registros = extraer_educacion(app_token=None)

    if dry_run:
        logger.info("[Educacion] Modo dry-run: mostrando primeros 2 registros.")
        for r in registros[:2]:
            logger.info(r)
        return {"fuente": "Educacion", "extraidos": len(registros), "cargados": 0}

    cargados = loader.load_educacion(registros)
    return {"fuente": "Educacion", "extraidos": len(registros), "cargados": cargados}


def main():
    parser = argparse.ArgumentParser(
        description="ETL pipeline de Kwesx AI"
    )
    parser.add_argument(
        "--fuente",
        choices=["ani", "upra", "ideam", "conectividad", "educacion", "all"],
        default="all",
        help="Dataset a procesar (default: all)",
    )
    parser.add_argument(
        "--desde",
        default=FECHA_INICIO,
        help=f"Fecha de inicio ISO 8601 (default: {FECHA_INICIO})",
    )
    parser.add_argument(
        "--dias-ideam",
        type=int,
        default=30,
        help="Días hacia atrás para carga de datos IDEAM (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extrae y transforma pero NO escribe en la BD",
    )
    args = parser.parse_args()

    logger.info(f"Kwesx AI — ETL Pipeline | Fecha: {date.today()}")
    logger.info(f"Fuente: {args.fuente} | Desde: {args.desde} | Dry-run: {args.dry_run}")

    # Crear/verificar tablas (solo si no es dry-run)
    loader = PostgresLoader()
    if not args.dry_run:
        loader.create_tables()

    resultados = []

    if args.fuente in ("ani", "all"):
        resultados.append(run_ani(loader, args.desde, args.dry_run))

    if args.fuente in ("upra", "all"):
        resultados.append(run_upra(loader, args.desde, args.dry_run))

    if args.fuente in ("ideam", "all"):
        resultados.append(run_ideam(loader, args.dias_ideam, args.dry_run))

    if args.fuente in ("conectividad", "all"):
        resultados.append(run_conectividad(loader, args.dry_run))

    if args.fuente in ("educacion", "all"):
        resultados.append(run_educacion(loader, args.dry_run))

    # Resumen final
    logger.info("")
    logger.info("=" * 60)
    logger.info("RESUMEN DEL PIPELINE")
    logger.info("=" * 60)
    for r in resultados:
        logger.info(
            f"  {r['fuente']:8s} → extraídos: {r['extraidos']:>7,} | "
            f"cargados: {r['cargados']:>7,}"
        )
    logger.success("Pipeline completado.")


if __name__ == "__main__":
    main()
