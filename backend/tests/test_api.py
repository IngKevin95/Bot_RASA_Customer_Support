"""
Tests del backend FastAPI.

Correr: cd backend && pytest tests/ -v
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services import session_store


@pytest.fixture(autouse=True)
def clear_store():
    """Limpia el session store entre tests para evitar estado compartido."""
    session_store._store.clear()
    session_store._created.clear()
    yield
    session_store._store.clear()
    session_store._created.clear()


@pytest.fixture
def rasa_ok(mocker):
    return mocker.patch(
        "app.api.routes.messages.rasa_client.send_message",
        return_value=[{"recipient_id": "test", "text": "Hola, en que te puedo ayudar?"}],
    )


@pytest.fixture
def rasa_down(mocker):
    import httpx
    return mocker.patch(
        "app.api.routes.messages.rasa_client.send_message",
        side_effect=httpx.ConnectError("RASA unreachable"),
    )


@pytest.mark.asyncio
async def test_send_message_ok(rasa_ok):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/messages",
            json={"session_id": "ses-001", "message": "hola"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "ses-001"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["sender"] == "bot"
    assert "Hola" in data["messages"][0]["text"]


@pytest.mark.asyncio
async def test_send_message_rasa_down(rasa_down):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/messages",
            json={"session_id": "ses-002", "message": "hola"},
        )
    assert resp.status_code == 503
    assert "no disponible" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_create_session():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert len(data["session_id"]) == 36  # UUID format


@pytest.mark.asyncio
async def test_get_history_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/sessions/unknown-session/history")
    assert resp.status_code == 200
    assert resp.json()["messages"] == []


@pytest.mark.asyncio
async def test_get_history_after_messages(rasa_ok):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/v1/messages", json={"session_id": "ses-hist", "message": "hola"})
        resp = await client.get("/api/v1/sessions/ses-hist/history")

    assert resp.status_code == 200
    messages = resp.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["sender"] == "user"
    assert messages[1]["sender"] == "bot"


@pytest.mark.asyncio
async def test_health_rasa_down(mocker):
    mocker.patch("app.api.routes.health.rasa_client.ping", return_value=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["services"]["rasa"] == "unreachable"


@pytest.mark.asyncio
async def test_health_rasa_ok(mocker):
    mocker.patch("app.api.routes.health.rasa_client.ping", return_value=True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_escalate_stub():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/escalate/ses-esc-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "ses-esc-001"
    assert data["provider"] == "stub"
    assert data["status"] == "simulated"
