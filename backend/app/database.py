"""
backend/app/database.py
=======================
Configuración del motor de base de datos y sesión SQLAlchemy.

Usa SQLAlchemy async (asyncpg) para que la API FastAPI pueda manejar
múltiples requests concurrentes sin bloquear el event loop.

Uso en endpoints
----------------
from backend.app.database import get_db

@router.get("/datos")
async def mi_endpoint(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MtuANI))
    return result.scalars().all()
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from backend.app.config import settings

# ── Motor async ────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.debug,      # True muestra todas las queries SQL en consola
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,       # verifica la conexión antes de usarla
)

# ── Fábrica de sesiones ────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """
    Dependency de FastAPI que provee una sesión de BD por request.

    Garantiza que la sesión se cierre correctamente incluso si hay errores.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
