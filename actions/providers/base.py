from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EscalationResult:
    success: bool
    provider: str
    message: str
    ticket_id: str | None = None


class EscalationProvider(ABC):
    """Contrato base para todos los proveedores de escalación."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def escalate(self, session_id: str, queue: str, context: dict) -> EscalationResult: ...

    @property
    def is_configured(self) -> bool:
        return True
