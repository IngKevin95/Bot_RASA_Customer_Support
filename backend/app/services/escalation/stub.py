import logging
from .base import EscalationProvider, EscalationResult

logger = logging.getLogger(__name__)


class StubProvider(EscalationProvider):
    @property
    def name(self) -> str:
        return "stub"

    def escalate(self, session_id: str, queue: str, context: dict) -> EscalationResult:
        logger.info("[stub] Escalacion simulada — session=%s queue=%s", session_id, queue)
        return EscalationResult(
            success=True,
            provider=self.name,
            message="Escalacion simulada (stub)",
            ticket_id=f"stub-{session_id[:8]}",
        )
