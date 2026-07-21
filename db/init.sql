-- ============================================================
-- Kwesx AI — Script inicial de base de datos
-- Se ejecuta automáticamente cuando el contenedor PostgreSQL
-- arranca por primera vez (docker-entrypoint-initdb.d).
-- ============================================================

-- Activar extensión PostGIS para datos geoespaciales
CREATE EXTENSION IF NOT EXISTS postgis;

-- Activar extensión uuid (por si acaso)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE 'Base de datos Kwesx AI inicializada con PostGIS.';
END $$;
