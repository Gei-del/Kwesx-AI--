# ============================================================
# Kwesx AI — Dockerfile para el backend FastAPI
# ============================================================

FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema (necesarias para psycopg2, geopandas)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código fuente
COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
