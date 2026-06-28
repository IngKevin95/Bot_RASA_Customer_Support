import logging
from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.services import rasa_client
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    services: dict[str, str] = {}

    rasa_ok = await rasa_client.ping()
    services["rasa"] = "ok" if rasa_ok else "unreachable"

    if settings.CHATWOOT_URL:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=3.0) as c:
                resp = await c.get(settings.CHATWOOT_URL)
                services["chatwoot"] = "ok" if resp.status_code < 500 else "unreachable"
        except httpx.RequestError:
            services["chatwoot"] = "unreachable"

    all_ok = all(v == "ok" for v in services.values())
    status = "ok" if all_ok else "degraded"

    return HealthResponse(status=status, services=services)
