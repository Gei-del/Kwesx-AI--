# Kwesx AI — Variables de entorno

Todas las variables se declaran en `.env` (desarrollo) o como secrets en Vercel/Render (producción).  
Nunca subir `.env` al repositorio — ya está en `.gitignore`.  
El archivo de referencia es `.env.example` en la raíz del proyecto.

---

## Base de datos (PostgreSQL)

| Variable | Ejemplo | Descripción |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://kwesx:pass@localhost:5432/kwesx_db` | URL para FastAPI (async) |
| `DATABASE_URL_SYNC` | `postgresql+psycopg2://kwesx:pass@localhost:5432/kwesx_db` | URL para ETL y scripts (sync) |
| `POSTGRES_USER` | `kwesx` | Usuario de PostgreSQL (Docker) |
| `POSTGRES_PASSWORD` | `kwesx_dev_2026` | Contraseña (cambiar en producción) |
| `POSTGRES_DB` | `kwesx_db` | Nombre de la base de datos |

**Producción:** usar conexión SSL, pool mínimo 5 conexiones, máximo 20.

---

## Backend (FastAPI)

| Variable | Ejemplo | Descripción |
|---|---|---|
| `API_HOST` | `0.0.0.0` | Host de escucha |
| `API_PORT` | `8000` | Puerto de escucha |
| `DEBUG` | `false` | `true` solo en desarrollo |
| `SECRET_KEY` | *(string aleatorio 64 chars)* | Clave para firmar tokens JWT (futuro) |
| `ALLOWED_ORIGINS` | `https://kwesx.vercel.app` | CORS: orígenes permitidos, separados por coma |
| `RATE_LIMIT_PER_MINUTE` | `120` | Límite global de peticiones por minuto |

Generar `SECRET_KEY` segura:
```bash
openssl rand -hex 32
```

---

## Frontend (Next.js)

Variables con prefijo `NEXT_PUBLIC_` son visibles en el browser. Las demás son solo server-side.

| Variable | Ejemplo | Descripción |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://kwesx-api.onrender.com` | URL del backend FastAPI |
| `NEXT_PUBLIC_VAPID_PUBLIC_KEY` | *(clave VAPID pública)* | Para push notifications (cuando se active) |
| `VAPID_PRIVATE_KEY` | *(clave VAPID privada)* | Server-side únicamente |
| `VAPID_CONTACT_EMAIL` | `admin@kwesx.ai` | Email de contacto VAPID |

**Vercel:** configurar `NEXT_PUBLIC_API_URL` en Project Settings → Environment Variables → Production.

---

## ETL (Pipeline de datos)

| Variable | Ejemplo | Descripción |
|---|---|---|
| `SOCRATA_APP_TOKEN` | *(token de Socrata)* | API token datos.gov.co — opcional pero recomendado |
| `ANI_DATASET_ID` | `8yi9-t44c` | Dataset ID de ANI en Socrata |
| `UPRA_DATASET_ID` | `gwbi-fnzs` | Dataset ID de UPRA en Socrata |
| `IDEAM_PRECIPITACION_ID` | `s54a-sgyg` | Dataset ID precipitación IDEAM |
| `IDEAM_TEMPERATURA_ID` | `sbwg-7ju4` | Dataset ID temperatura IDEAM |
| `IDEAM_CATALOGO_ID` | `hp9r-jxuu` | Dataset ID catálogo estaciones IDEAM |
| `ETL_BATCH_SIZE` | `10000` | Registros por lote (Socrata max: 50000) |
| `ETL_FECHA_INICIO` | `2021-01-01` | Fecha de inicio para carga inicial |
| `ETL_FECHA_FIN` | `2026-06-30` | Fecha de fin para carga inicial |

**Obtener token Socrata (gratis):**
1. Ir a https://data.socrata.com/profile
2. Crear cuenta → API Keys → Create new key
3. Pegar en `SOCRATA_APP_TOKEN`

Sin token: funciona, pero límite de 1000 req/hora. Con token: 100,000 req/hora.

---

## ML (Machine Learning)

| Variable | Ejemplo | Descripción |
|---|---|---|
| `ML_MODELS_PATH` | `ml/models` | Directorio donde se guardan los `.pkl` |
| `ML_RANDOM_SEED` | `2026` | Semilla aleatoria para reproducibilidad |
| `ML_N_JOBS` | `-1` | Núcleos a usar (`-1` = todos) |
| `ML_FORECAST_HORIZON` | `6` | Meses de pronóstico por defecto |

---

## Docker Compose

Las variables para Docker se leen automáticamente desde `.env` en la raíz. Si `.env` no existe, Docker Compose usa los defaults definidos con `${VAR:-default}` en `docker-compose.yml`.

```bash
# Mínimo para desarrollo con Docker
POSTGRES_USER=kwesx
POSTGRES_PASSWORD=kwesx_dev_2026
POSTGRES_DB=kwesx_db
DATABASE_URL=postgresql+asyncpg://kwesx:kwesx_dev_2026@db:5432/kwesx_db
DATABASE_URL_SYNC=postgresql+psycopg2://kwesx:kwesx_dev_2026@db:5432/kwesx_db
```

---

## Setup rápido

```bash
# 1. Copiar .env.example a .env
cp .env.example .env

# 2. Editar con tus valores (mínimo requerido: DB_URL)
nano .env   # o code .env

# 3. Verificar que el backend lee las variables
cd backend
python -c "from app.config import settings; print(settings.DATABASE_URL)"
```

---

## Checklist antes de producción

- [ ] `SECRET_KEY` generada con `openssl rand -hex 32` (no el valor de ejemplo)
- [ ] `POSTGRES_PASSWORD` no es `kwesx_dev_2026`
- [ ] `DEBUG=false`
- [ ] `ALLOWED_ORIGINS` apunta solo al dominio de producción
- [ ] `NEXT_PUBLIC_API_URL` apunta al backend en Render (no a localhost)
- [ ] `SOCRATA_APP_TOKEN` configurado para evitar rate limit
- [ ] `.env` en `.gitignore` ✅ (ya está por defecto)
- [ ] Secrets cargados en Vercel y Render como variables de entorno (no en código)
