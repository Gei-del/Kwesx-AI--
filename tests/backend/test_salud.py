"""
Kwesx AI — Tests del endpoint /salud (health check)
"""

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
@pytest.mark.unit
async def test_health_check_returns_200():
    """El endpoint /salud debe retornar 200."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/salud")

    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.unit
async def test_health_check_response_structure():
    """El endpoint /salud debe retornar la estructura correcta."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/salud")

    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "healthy", "running")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_root_returns_api_info():
    """El endpoint raíz / debe retornar información de la API."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code in (200, 307)  # 307 si hay redirect a /docs
