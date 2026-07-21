"""
backend/app/models/mtu.py
==========================
Modelos SQLAlchemy del Modelo Territorial Unificado (MTU).

Estructura de tablas
--------------------
mtu_ani    — Tráfico vehicular por peaje (fuente ANI)
mtu_upra   — Índice de precios de insumos agrícolas (fuente UPRA)
mtu_ideam  — Variables climáticas por estación (fuente IDEAM)

Diseño
------
- Cada tabla tiene las columnas compartidas del MTU (codigo_dane, departamento,
  municipio, latitud, longitud, fecha, sector, fuente).
- Más las columnas específicas de cada fuente.
- Las restricciones UNIQUE evitan duplicados en cargas incrementales.
- Los índices en codigo_dane + fecha aceleran las consultas del dashboard.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Text,
    UniqueConstraint, Index, Boolean
)
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    """Base declarativa compartida por todos los modelos."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# MTU — ANI Tráfico Vehicular en Peajes
# ─────────────────────────────────────────────────────────────────────────────

class MtuANI(Base):
    """
    Registros de tráfico vehicular en peajes de la red vial concesionada (ANI).

    Un registro = un peaje, una categoría de tarifa, un período (desde–hasta).
    """
    __tablename__ = "mtu_ani"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Columnas MTU compartidas ──
    codigo_dane  = Column(String(5),  nullable=True,  index=True)
    departamento = Column(String(100), nullable=True)
    municipio    = Column(String(100), nullable=True)
    latitud      = Column(Float,       nullable=True)
    longitud     = Column(Float,       nullable=True)
    fecha        = Column(Date,        nullable=True,  index=True)  # = fecha_inicio
    sector       = Column(String(50),  nullable=False, default="transporte")
    fuente       = Column(String(50),  nullable=False, default="ANI")

    # ── Columnas específicas ANI ──
    idpeaje          = Column(String(50),  nullable=True)
    peaje            = Column(String(200), nullable=True)
    categoria_tarifa = Column(String(50),  nullable=True)
    fecha_inicio     = Column(Date,        nullable=True)
    fecha_fin        = Column(Date,        nullable=True)
    valor_tarifa     = Column(Float,       nullable=True)
    cantidad_trafico = Column(Integer,     nullable=True)
    cantidad_evasores= Column(Integer,     nullable=True)
    cantidad_exentos = Column(Integer,     nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        # Evitar duplicados: mismo peaje, mismo período, misma categoría
        UniqueConstraint(
            "idpeaje", "fecha_inicio", "categoria_tarifa",
            name="uq_ani_peaje_periodo_categoria",
        ),
        # Índice compuesto para queries frecuentes: por DANE + fecha
        Index("ix_ani_dane_fecha", "codigo_dane", "fecha"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# MTU — UPRA Índice de Precios de Insumos Agrícolas
# ─────────────────────────────────────────────────────────────────────────────

class MtuUPRA(Base):
    """
    Índice mensual de precios de insumos agrícolas (UPRA).

    Un registro = un mes. Índice nacional, sin desglose geográfico.
    codigo_dane = '00' (convenio Kwesx AI para datos nacionales).
    """
    __tablename__ = "mtu_upra"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Columnas MTU compartidas ──
    codigo_dane  = Column(String(5),   nullable=False, default="00", index=True)
    departamento = Column(String(100), nullable=False, default="Nacional")
    municipio    = Column(String(100), nullable=False, default="Colombia")
    latitud      = Column(Float,       nullable=True,  default=4.5709)
    longitud     = Column(Float,       nullable=True,  default=-74.2973)
    fecha        = Column(Date,        nullable=False, index=True)
    sector       = Column(String(50),  nullable=False, default="agropecuario")
    fuente       = Column(String(50),  nullable=False, default="UPRA")

    # ── Columnas específicas UPRA ──
    indice_total        = Column(Float, nullable=True)
    total_fertilizantes = Column(Float, nullable=True)
    total_plaguicidas   = Column(Float, nullable=True)
    total_otros         = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        # Un solo registro por mes
        UniqueConstraint("fecha", name="uq_upra_fecha"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# MTU — IDEAM Variables Climáticas
# ─────────────────────────────────────────────────────────────────────────────

class MtuIDEAM(Base):
    """
    Mediciones climáticas de la red de estaciones del IDEAM.

    Un registro = una estación, un sensor, una fecha/hora.
    tipo_variable discrimina precipitación vs. temperatura.
    """
    __tablename__ = "mtu_ideam"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Columnas MTU compartidas ──
    codigo_dane  = Column(String(5),   nullable=True,  index=True)
    departamento = Column(String(100), nullable=True)
    municipio    = Column(String(100), nullable=True)
    latitud      = Column(Float,       nullable=True)
    longitud     = Column(Float,       nullable=True)
    fecha        = Column(Date,        nullable=True,  index=True)
    sector       = Column(String(50),  nullable=False, default="climatico")
    fuente       = Column(String(50),  nullable=False, default="IDEAM")

    # ── Columnas específicas IDEAM ──
    codigo_estacion  = Column(String(20),  nullable=True)
    nombre_estacion  = Column(String(200), nullable=True)
    codigo_sensor    = Column(String(50),  nullable=True)
    tipo_variable    = Column(String(50),  nullable=True)  # 'precipitacion_mm' | 'temperatura_c'
    valor_observado  = Column(Float,       nullable=True)
    unidad_medida    = Column(String(30),  nullable=True)
    zona_hidrografica= Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        # Un registro por estación/sensor/fecha (las tablas IDEAM actualizan cada 10 min/1 hora)
        UniqueConstraint(
            "codigo_estacion", "codigo_sensor", "fecha",
            name="uq_ideam_estacion_sensor_fecha",
        ),
        # Índice para queries geoespaciales y temporales
        Index("ix_ideam_dane_fecha", "codigo_dane", "fecha"),
        Index("ix_ideam_tipo_fecha",  "tipo_variable", "fecha"),
    )


# -----------------------------------------------------------------------------
# MTU -- DANE/MinTIC Conectividad a Internet
# -----------------------------------------------------------------------------

class MtuConectividad(Base):
    """
    Conectividad a Internet por municipio.
    Fuente: DANE Encuesta de Calidad de Vida + MinTIC Brecha Digital.

    Un registro = un municipio, un anio, un tipo de conexion.
    """
    __tablename__ = "mtu_conectividad"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # -- Columnas MTU compartidas --
    codigo_dane  = Column(String(5),   nullable=False, index=True)
    departamento = Column(String(100), nullable=True)
    municipio    = Column(String(100), nullable=True)
    latitud      = Column(Float,       nullable=True)
    longitud     = Column(Float,       nullable=True)
    fecha        = Column(Date,        nullable=True, index=True)
    sector       = Column(String(50),  nullable=False, default="tecnologia")
    fuente       = Column(String(50),  nullable=False, default="DANE-MinTIC")

    # -- Columnas especificas conectividad --
    anio                  = Column(Integer, nullable=False)
    pct_hogares_internet  = Column(Float,   nullable=True)  # 0-100
    pct_hogares_celular   = Column(Float,   nullable=True)  # 0-100
    pct_hogares_pc        = Column(Float,   nullable=True)  # 0-100
    tipo_conexion         = Column(String(50), nullable=True)  # 'fija' | 'movil' | 'mixta'
    velocidad_mbps        = Column(Float,   nullable=True)
    poblacion             = Column(Integer, nullable=True)
    zona                  = Column(String(20), nullable=True)  # 'urbana' | 'rural'

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "codigo_dane", "anio", "tipo_conexion", "zona",
            name="uq_conectividad_dane_anio_tipo_zona",
        ),
        Index("ix_conectividad_dane_anio", "codigo_dane", "anio"),
    )


# -----------------------------------------------------------------------------
# MTU -- MEN Cobertura Educativa
# -----------------------------------------------------------------------------

class MtuEducacion(Base):
    """
    Cobertura educativa por municipio y nivel.
    Fuente: Ministerio de Educacion Nacional (MEN) -- SIMAT.

    Un registro = un municipio, un nivel educativo, un anio.
    """
    __tablename__ = "mtu_educacion"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # -- Columnas MTU compartidas --
    codigo_dane  = Column(String(5),   nullable=False, index=True)
    departamento = Column(String(100), nullable=True)
    municipio    = Column(String(100), nullable=True)
    latitud      = Column(Float,       nullable=True)
    longitud     = Column(Float,       nullable=True)
    fecha        = Column(Date,        nullable=True, index=True)
    sector       = Column(String(50),  nullable=False, default="educacion")
    fuente       = Column(String(50),  nullable=False, default="MEN")

    # -- Columnas especificas educacion --
    anio                    = Column(Integer, nullable=False)
    nivel_educativo         = Column(String(50),  nullable=True)  # preescolar, primaria, secundaria, media
    matriculados            = Column(Integer,      nullable=True)
    matriculados_oficial    = Column(Integer,      nullable=True)
    matriculados_privado    = Column(Integer,      nullable=True)
    tasa_cobertura_neta     = Column(Float,        nullable=True)  # 0-100
    tasa_cobertura_bruta    = Column(Float,        nullable=True)  # 0-100
    tasa_aprobacion         = Column(Float,        nullable=True)  # 0-100
    tasa_desercion          = Column(Float,        nullable=True)  # 0-100
    zona                    = Column(String(20),   nullable=True)  # 'total' | 'urbana' | 'rural'

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "codigo_dane", "anio", "nivel_educativo", "zona",
            name="uq_educacion_dane_anio_nivel_zona",
        ),
        Index("ix_educacion_dane_anio", "codigo_dane", "anio"),
    )
