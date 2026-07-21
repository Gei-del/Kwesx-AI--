# Kwesx AI — Guía de Despliegue Local (VS Code)

Guía paso a paso para levantar el proyecto desde cero en Visual Studio Code.

---

## Requisitos previos

| Herramienta | Versión mínima | Para qué |
|---|---|---|
| Python | 3.11 | Backend + ML |
| Node.js | 18 LTS | Frontend |
| Docker Desktop | 4.x | PostgreSQL |
| VS Code | 1.90+ | Editor |

Extensiones VS Code recomendadas: `Python`, `ESLint`, `Tailwind CSS IntelliSense`, `Docker`.

---

## 1. Clonar y abrir el proyecto

```bash
cd "Kwesx IA"
code .
```

---

## 2. Backend Python — Entorno virtual

```bash
# Crear el entorno virtual (ya existe en el proyecto como venv/)
python -m venv venv

# Activar (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activar (Windows CMD)
.\venv\Scripts\activate.bat

# Instalar dependencias
pip install -r requirements.txt
```

---

## 3. Variables de entorno

```bash
# Copiar la plantilla
copy .env.example .env
```

Editar `.env` con los valores reales:

```env
DATABASE_URL=postgresql+asyncpg://kwesx:kwesx2026@localhost:5432/kwesx_db
DATABASE_URL_SYNC=postgresql+psycopg2://kwesx:kwesx2026@localhost:5432/kwesx_db
SECRET_KEY=kwesx-ai-secret-2026
ENVIRONMENT=development
DEBUG=true
```

---

## 4. Levantar la base de datos (Docker)

```bash
# Iniciar PostgreSQL con PostGIS
docker compose up -d db

# Verificar que esté activo
docker compose ps
# → kwesx_db   Up (healthy)
```

Las tablas se crean **automáticamente** al arrancar el backend por primera vez (`lifespan` en `main.py`).

---

## 5. Cargar datos (ETL)

```bash
# Pipeline completo (ANI + UPRA + IDEAM + Conectividad + Educación)
make etl

# O fuente por fuente
make etl-ani
make etl-upra
make etl-ideam
make etl-conectividad
make etl-educacion
```

> Los extractores intentan la API real de datos.gov.co. Si no hay token o la API no responde, generan **datos sintéticos realistas** automáticamente (marcados como `fuente=X-SIMULADO`).

---

## 6. Iniciar el backend FastAPI

```bash
# Opción A: desde terminal en VS Code (con el venv activo)
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Opción B: con Make
# (requiere que Docker esté activo)
# docker compose up -d api
```

Verificar: `http://localhost:8000/docs` → debe mostrar Swagger UI con todos los endpoints.

---

## 7. Frontend Next.js

```bash
cd frontend
npm install
npm run dev
```

Verificar: `http://localhost:3000` → dashboard de Kwesx AI.

---

## 8. Entrenar modelos ML (opcional pero recomendado)

```bash
# Desde la raíz del proyecto (con venv activo)
make train-advanced

# Calcular métricas de validación
make validate
```

Los modelos se guardan en `ml/models/`. Sin ellos, los endpoints `/ml/...` devuelven `modelo_disponible: false` con mensaje de ayuda.

---

## 9. Verificación rápida

| Endpoint | Resultado esperado |
|---|---|
| `GET /` | `{"estado": "activo", ...}` |
| `GET /datos/resumen` | Conteos de todas las tablas |
| `GET /datos/conectividad` | Lista de municipios con cobertura internet |
| `GET /datos/educacion` | Tasas de cobertura por nivel |
| `POST /asistente/chat` body `{"texto":"¿cómo está el clima?"}` | Respuesta NLP |
| `GET /recomendaciones` | Lista de recomendaciones priorizadas |
| `GET /ml/validacion` | Métricas del modelo (o mensaje de no entrenado) |

---

## 10. Estructura de comandos Make

```
make setup          → Configura el proyecto desde cero
make etl            → Carga todos los datasets
make train          → Entrena modelo IVT básico
make train-advanced → Entrena ensemble, clustering, forecasting, etc.
make validate       → Genera métricas de validación ML
make test           → Corre la suite de pruebas
make lint           → Verifica calidad del código
make clean          → Elimina caché de Python
make frontend-dev   → Levanta el frontend en modo desarrollo
```

---

## Solución de problemas frecuentes

**"relation X does not exist"**  
→ Las tablas no se crearon. Verificar que el backend arrancó sin errores. Si persiste: `docker compose restart api`.

**"Module not found: backend.app..."**  
→ Ejecutar siempre desde la raíz del proyecto, con el venv activo y desde la carpeta `Kwesx IA/`.

**Frontend: "Cannot read properties of null"**  
→ El backend no está corriendo. Verificar `http://localhost:8000/docs`.

**"slow_api not found" en logs**  
→ Es una advertencia, no un error. Rate limiting está desactivado pero la API funciona normalmente.

**Tailwind clases no aparecen**  
→ `cd frontend && npm install` y reiniciar `npm run dev`.
