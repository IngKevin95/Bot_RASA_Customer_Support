import logging
from fastapi import APIRouter
from app.models.schemas import EscalationResponse
from app.services.escalation import get_provider
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/escalate/{session_id}", response_model=EscalationResponse)
async def escalate(session_id: str):
    provider = get_provider()
    result = provider.escalate(
        session_id=session_id,
        queue=settings.ESCALATION_QUEUE,
        context={},
    )

    logger.info(
        "Escalacion via %s — success=%s ticket=%s",
        result.provider, result.success, result.ticket_id,
    )

    status = "escalated" if result.success else "failed"
    if result.provider == "stub":
        status = "simulated"

    return EscalationResponse(
        session_id=session_id,
        provider=result.provider,
        status=status,
        ticket_id=result.ticket_id,
    )
