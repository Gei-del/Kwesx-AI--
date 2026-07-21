# Kwesx AI — Documentación de Base de Datos

**Motor:** PostgreSQL 15 + PostGIS 3.4  
**ORM:** SQLAlchemy 2.0 (async)  
**Migraciones:** Alembic 1.13  
**Creación automática:** `Base.metadata.create_all()` en lifespan de FastAPI

---

## Diagrama Entidad-Relación

```mermaid
erDiagram
    MTU_ANI {
        int id PK
        string codigo_dane
        string departamento
        string municipio
        float latitud
        float longitud
        string peaje
        string categoria_tarifa
        date fecha_inicio
        date fecha_fin
        float valor_tarifa
        int cantidad_trafico
        int cantidad_evasores
        int cantidad_exentos
        string fuente
    }

    MTU_UPRA {
        int id PK
        date fecha
        float indice_total
        float var_mensual_pct
        float fertilizantes
        float plaguicidas
        float semillas
        float combustible
        string fuente
    }

    MTU_IDEAM {
        int id PK
        string codigo_dane
        string departamento
        string municipio
        float latitud
        float longitud
        date fecha
        string nombre_estacion
        string tipo_variable
        float valor_observado
        string unidad_medida
        string zona_hidrografica
        string fuente
    }

    MTU_CONECTIVIDAD {
        int id PK
        string codigo_dane
        string departamento
        string municipio
        float pct_hogares_internet
        string tipo_conexion
        int anio
        string zona
        string fuente
    }

    MTU_EDUCACION {
        int id PK
        string codigo_dane
        string departamento
        string municipio
        float tasa_cobertura_neta
        string nivel_educativo
        int anio
        string zona
        string fuente
    }
```

---

## Tablas

### `mtu_ani` — Tráfico Vehicular ANI

| Columna | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | SERIAL PK | NO | ID autoincremental |
| `codigo_dane` | VARCHAR(8) | YES | Código DANE del municipio |
| `departamento` | VARCHAR(64) | YES | Nombre del departamento |
| `municipio` | VARCHAR(64) | YES | Nombre del municipio |
| `latitud` | FLOAT | YES | Coordenada geográfica |
| `longitud` | FLOAT | YES | Coordenada geográfica |
| `peaje` | VARCHAR(128) | NO | Nombre del punto de peaje |
| `categoria_tarifa` | VARCHAR(8) | NO | Categoría del vehículo (I, II, III...) |
| `fecha_inicio` | DATE | NO | Inicio del período de medición |
| `fecha_fin` | DATE | NO | Fin del período de medición |
| `valor_tarifa` | FLOAT | YES | Tarifa en pesos COP |
| `cantidad_trafico` | INTEGER | NO | Vehículos que pagaron |
| `cantidad_evasores` | INTEGER | YES | Vehículos que evadieron |
| `cantidad_exentos` | INTEGER | YES | Vehículos exentos |
| `fuente` | VARCHAR(32) | NO | `ANI` o `ANI-SIMULADO` |

**Índice único:** `(peaje, categoria_tarifa, fecha_inicio, fecha_fin)`

---

### `mtu_upra` — Precios de Insumos Agrícolas

| Columna | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | SERIAL PK | NO | ID autoincremental |
| `fecha` | DATE | NO | Mes de referencia |
| `indice_total` | FLOAT | NO | Índice total de precios (base 100) |
| `var_mensual_pct` | FLOAT | YES | Variación porcentual mensual |
| `fertilizantes` | FLOAT | YES | Subíndice fertilizantes |
| `plaguicidas` | FLOAT | YES | Subíndice plaguicidas |
| `semillas` | FLOAT | YES | Subíndice semillas |
| `combustible` | FLOAT | YES | Subíndice combustible |
| `fuente` | VARCHAR(32) | NO | `UPRA` o `X-SIMULADO` |

**Índice único:** `(fecha)`

---

### `mtu_ideam` — Variables Climáticas

| Columna | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | SERIAL PK | NO | ID autoincremental |
| `codigo_dane` | VARCHAR(8) | YES | Código DANE |
| `departamento` | VARCHAR(64) | YES | Departamento |
| `municipio` | VARCHAR(64) | YES | Municipio |
| `latitud` | FLOAT | YES | Latitud de la estación |
| `longitud` | FLOAT | YES | Longitud de la estación |
| `fecha` | DATE | NO | Fecha de medición |
| `nombre_estacion` | VARCHAR(128) | NO | Nombre de la estación hidrometeorológica |
| `tipo_variable` | VARCHAR(32) | NO | `precipitacion` o `temperatura` |
| `valor_observado` | FLOAT | NO | Valor medido |
| `unidad_medida` | VARCHAR(16) | NO | `mm` o `°C` |
| `zona_hidrografica` | VARCHAR(64) | YES | Zona hidrográfica IDEAM |
| `fuente` | VARCHAR(32) | NO | `IDEAM` o `IDEAM-SIMULADO` |

**Índice único:** `(nombre_estacion, fecha, tipo_variable)`

---

### `mtu_conectividad` — Brecha Digital

| Columna | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | SERIAL PK | NO | ID autoincremental |
| `codigo_dane` | VARCHAR(8) | NO | Código DANE |
| `departamento` | VARCHAR(64) | NO | Departamento |
| `municipio` | VARCHAR(64) | NO | Municipio |
| `pct_hogares_internet` | FLOAT | NO | % hogares con acceso a internet |
| `tipo_conexion` | VARCHAR(32) | NO | `fija`, `movil`, `total` |
| `anio` | INTEGER | NO | Año del dato |
| `zona` | VARCHAR(16) | YES | `urbana`, `rural` |
| `fuente` | VARCHAR(32) | NO | `DANE-MinTIC` o `X-SIMULADO` |

**Índice único:** `(codigo_dane, anio, tipo_conexion, zona)`

---

### `mtu_educacion` — Cobertura Educativa

| Columna | Tipo | Nullable | Descripción |
|---|---|---|---|
| `id` | SERIAL PK | NO | ID autoincremental |
| `codigo_dane` | VARCHAR(8) | NO | Código DANE |
| `departamento` | VARCHAR(64) | NO | Departamento |
| `municipio` | VARCHAR(64) | NO | Municipio |
| `tasa_cobertura_neta` | FLOAT | NO | Tasa de cobertura neta (%) |
| `nivel_educativo` | VARCHAR(32) | NO | `preescolar`, `primaria`, `secundaria`, `media` |
| `anio` | INTEGER | NO | Año escolar |
| `zona` | VARCHAR(16) | YES | `urbana`, `rural` |
| `fuente` | VARCHAR(32) | NO | `MEN-SIMAT` o `X-SIMULADO` |

**Índice único:** `(codigo_dane, anio, nivel_educativo, zona)`

---

## Creación de tablas

Las tablas se crean **automáticamente** al arrancar el backend:

```python
# backend/app/main.py — lifespan
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

También se pueden crear manualmente desde el ETL:

```bash
python -m etl.pipeline --fuente all --dry-run  # verificar sin escribir
python -m etl.pipeline --fuente all             # cargar todos los datasets
```

---

## Conexión

```python
# Configuración en backend/app/database.py
# Async (FastAPI)
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/kwesx_db"

# Sync (ETL/scripts)
DATABASE_URL_SYNC = "postgresql+psycopg2://user:pass@localhost:5432/kwesx_db"
```

### Pool de conexiones (async)

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,   # verifica conexión antes de usar
    echo=False,
)
```

---

## Convenciones

- Prefijo de tabla: `mtu_` (Modelo Territorial Único)
- Nombres en snake_case
- Primary keys: `SERIAL` (autoincremental)
- Fechas: `DATE` para fechas, `TIMESTAMP WITH TIME ZONE` para datetimes exactos
- Texto corto: `VARCHAR(n)` con límite adecuado
- Coordenadas: `FLOAT` (no `GEOMETRY` — PostGIS solo para consultas espaciales futuras)
- `fuente`: siempre indica el origen del dato; sufijo `*-SIMULADO` si es sintético

---

## Mantenimiento

```bash
# Ver conteo de registros por tabla
psql -U kwesx -d kwesx_db -c "SELECT 'mtu_ani' as tabla, COUNT(*) FROM mtu_ani UNION ALL SELECT 'mtu_upra', COUNT(*) FROM mtu_upra UNION ALL SELECT 'mtu_ideam', COUNT(*) FROM mtu_ideam;"

# Vaciar y recargar una tabla
psql -U kwesx -d kwesx_db -c "TRUNCATE mtu_upra;"
python -m etl.pipeline --fuente upra

# Backup
pg_dump -U kwesx -d kwesx_db > backup_$(date +%Y%m%d).sql
```
