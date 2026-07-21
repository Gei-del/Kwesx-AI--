# Kwesx AI — ETL Pipeline

**Flujo:** Extraccion (Socrata API) -> Transformacion -> Carga (PostgreSQL)
**Fuentes:** ANI · UPRA · IDEAM · DANE/MinTIC · MEN-SIMAT
**Documentacion completa:** [docs/ETL.md](../docs/ETL.md)

---

## Correr el ETL

```bash
# Desde la raiz del proyecto, con venv activo

make etl                           # Todos los datasets
make etl-upra                      # Solo UPRA
make etl-ani                       # Solo ANI
make etl-ideam                     # Solo IDEAM
python -m etl.pipeline --dry-run   # Sin escribir en BD
```

---

## Estructura

```
etl/
├── config.py         # Fechas de inicio, variables de configuracion
├── pipeline.py       # Orquestador principal
├── extractors/       # Conectores a las APIs de Socrata
├── transformers/     # Normalizacion al schema MTU
└── loaders/          # Carga incremental a PostgreSQL (UPSERT)
```

---

## Patron de fallback

Si la API de datos.gov.co no esta disponible, el extractor genera datos sinteticos calibrados
con estadisticas reales (campo `fuente` = `"*-SIMULADO"`).

---

## Agregar una nueva fuente

Ver la guia paso a paso en [docs/ETL.md](../docs/ETL.md#agregar-una-nueva-fuente-de-datos).
