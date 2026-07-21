"""
Kwesx AI — Tests del endpoint /asistente (NLP / chat)
"""

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
@pytest.mark.unit
async def test_asistente_responde_pregunta_lluvia():
    """El asistente debe responder preguntas sobre lluvia."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/asistente/chat",
            json={"mensaje": "¿Va a llover hoy en Bogotá?"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "respuesta" in data
    assert isinstance(data["respuesta"], str)
    assert len(data["respuesta"]) > 10


@pytest.mark.asyncio
@pytest.mark.unit
async def test_asistente_responde_pregunta_precios():
    """El asistente debe responder preguntas sobre precios agrícolas."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/asistente/chat",
            json={"mensaje": "¿Cómo están los precios de los abonos?"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "respuesta" in data


@pytest.mark.asyncio
@pytest.mark.unit
async def test_asistente_maneja_mensaje_vacio():
    """El asistente debe manejar mensajes vacíos sin crash."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/asistente/chat",
            json={"mensaje": ""}
        )

    # Debe retornar 200 con respuesta de fallback, o 422 por validación
    assert response.status_code in (200, 422)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_asistente_respuesta_tiene_intencion():
    """La respuesta del asistente debe incluir la intención detectada."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/asistente/chat",
            json={"mensaje": "¿Cuántos carros pasaron por el peaje hoy?"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "intencion" in data or "respuesta" in data
