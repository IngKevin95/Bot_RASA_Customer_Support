import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_message(session_id: str, message: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{settings.RASA_URL}/webhooks/rest/webhook",
            json={"sender": session_id, "message": message},
        )
        resp.raise_for_status()
        return resp.json()


async def ping() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(settings.RASA_URL)
            return resp.status_code < 500
    except httpx.RequestError:
        return False
