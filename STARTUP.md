# Kwesx AI — Cómo levantar el proyecto en Windows

> **Importante:** Tu computador ya tiene PostgreSQL 17 instalado en el puerto 5432.
> El proyecto usa Docker para correr su propia base de datos en el puerto **5433**,
> así no hay conflicto entre los dos.

---

## Lo que necesitas tener instalado

- **Docker Desktop** — descarga en https://www.docker.com/products/docker-desktop/
  - Después de instalar, ábrelo y espera a que el ícono de la ballena aparezca en la barra de tareas
- **Python 3.11** con el entorno virtual del proyecto (`venv`)
- **Node.js 18+** — descarga en https://nodejs.org/

---

## Paso 1 — Abrir Git Bash en la carpeta del proyecto

Abre **Git Bash** (no CMD, no PowerShell) y navega a la carpeta:

```bash
cd ~/Downloads/Kwesx\ IA
```

Activa el entorno virtual de Python:

```bash
source venv/Scripts/activate
```

Deberías ver `(venv)` al inicio de la línea. Eso significa que está activo.

---

## Paso 2 — Levantar la base de datos con Docker

Con Docker Desktop abierto, ejecuta en Git Bash:

```bash
docker compose up -d db
```

Espera 15-20 segundos y verifica que esté lista:

```bash
docker compose ps
```

Debes ver algo así:

```
NAME        STATUS
kwesx_db    Up (healthy)
```

> Si dice `Up (starting)`, espera 10 segundos más y vuelve a ejecutar `docker compose ps`.

La base de datos ya quedó lista. Docker ejecuta el script `db/init.sql` automáticamente — **no necesitas correr psql manualmente**.

---

## Paso 3 — Levantar el Backend (FastAPI)

Abre una **segunda ventana de Git Bash** en la misma carpeta. Activa el venv:

```bash
cd ~/Downloads/Kwesx\ IA
source venv/Scripts/activate
```

Inicia el servidor:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Debes ver al final:
```
INFO:     Application startup complete.
```

Sin WARNING de PostgreSQL — el puerto 5433 evita el conflicto con tu PostgreSQL 17.

Abre en el navegador: http://localhost:8000/docs

---

## Paso 4 — Cargar los datos (ETL)

Abre una **tercera ventana de Git Bash** con el venv activo:

```bash
cd ~/Downloads/Kwesx\ IA
source venv/Scripts/activate
python -m etl.run_all
```

Esto descarga datos reales de ANI, UPRA, IDEAM, Conectividad y Educación desde datos.gov.co.
Si alguna API no responde, el sistema usa datos de respaldo automáticamente.

---

## Paso 5 — Levantar el Frontend (Next.js)

Abre una **cuarta ventana de Git Bash**:

```bash
cd ~/Downloads/Kwesx\ IA/frontend
npm run dev
```

Abre en el navegador: http://localhost:3000

---

## Resumen — 4 terminales en paralelo

| Terminal | Comando | Para qué |
|---|---|---|
| 1 | `docker compose up -d db` | Base de datos (se queda corriendo en background) |
| 2 | `uvicorn backend.app.main:app --reload ...` | API backend FastAPI |
| 3 | `python -m etl.run_all` | Carga de datos (solo una vez, luego puedes cerrarla) |
| 4 | `npm run dev` | Interfaz web |

---

## Verificar que todo funciona

Abre estas URLs en el navegador:

| URL | Qué deberías ver |
|---|---|
| http://localhost:8000 | `{"status":"ok","proyecto":"Kwesx AI",...}` |
| http://localhost:8000/salud/etl | Tablas con cantidad de registros cargados |
| http://localhost:8000/docs | Documentación interactiva de la API |
| http://localhost:3000 | Dashboard principal de Kwesx AI |

---

## Conectarse a la base de datos manualmente (opcional)

Si quieres inspeccionar la base de datos con psql, usa el puerto 5433:

```bash
"/c/Program Files/PostgreSQL/17/bin/psql.exe" -h localhost -p 5433 -U kwesx -d kwesx_db
```

Contraseña: `kwesx_dev_2026`

O usa pgAdmin / DBeaver apuntando a:
- Host: `localhost`
- Puerto: `5433`
- Usuario: `kwesx`
- Contraseña: `kwesx_dev_2026`
- Base de datos: `kwesx_db`

---

## Detener el proyecto

```bash
# Detener la base de datos Docker
docker compose down

# En las otras terminales: presiona Ctrl+C
```

---

## Solución de problemas frecuentes en Windows

### El WARNING de PostgreSQL sigue apareciendo
**Causa:** Docker todavía no terminó de arrancar.
**Solución:** Espera a que `docker compose ps` muestre `Up (healthy)` antes de iniciar uvicorn.

### `docker compose up` da error de puerto 5433 ocupado
**Causa:** Algo ya está usando el puerto 5433 en tu sistema.
**Solución:** Cambia `DB_PORT=5433` a `DB_PORT=5434` en el archivo `.env` y actualiza el puerto en `DATABASE_URL` y `DATABASE_URL_SYNC` también.

### `source venv/Scripts/activate` no funciona
**Causa:** El venv fue creado con una ruta diferente o no existe.
**Solución:** Créalo desde cero:
```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

### `npm run dev` dice que falta algún módulo
**Solución:**
```bash
cd frontend
npm install
npm run dev
```

### La página en localhost:3000 no muestra datos
**Causa:** El backend no está corriendo o el ETL no cargó datos todavía.
**Solución:** Verifica que uvicorn esté activo (Paso 3) y que http://localhost:8000 responda.

---

## Puertos usados por el proyecto

| Puerto | Servicio |
|---|---|
| 5432 | Tu PostgreSQL 17 nativo (no lo toques) |
| 5433 | PostgreSQL de Docker para Kwesx AI |
| 8000 | Backend FastAPI |
| 3000 | Frontend Next.js |
