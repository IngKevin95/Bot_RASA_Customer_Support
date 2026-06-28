import logging
from .base import EscalationProvider, EscalationResult

logger = logging.getLogger(__name__)


class StubProvider(EscalationProvider):
    """
    Provider de prueba — simula la escalación sin integración real.
    Útil en desarrollo local o cuando no hay proveedor configurado.
    """

    @property
    def name(self) -> str:
        return "stub"

    def escalate(self, session_id: str, queue: str, context: dict) -> EscalationResult:
        logger.info(
            "[stub] Escalación simulada — session=%s queue=%s",
            session_id,
            queue,
        )
        return EscalationResult(
            success=True,
            provider=self.name,
            message="Escalación simulada correctamente (stub)",
            ticket_id=f"stub-{session_id[:8]}",
        )
