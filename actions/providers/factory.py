import logging
import os

from .base import EscalationProvider
from .stub import StubProvider
from .chatwoot import ChatwootProvider
from .genesys import GenesysProvider

logger = logging.getLogger(__name__)

_PROVIDERS: dict[str, type[EscalationProvider]] = {
    "stub": StubProvider,
    "chatwoot": ChatwootProvider,
    "genesys": GenesysProvider,
}


def get_provider() -> EscalationProvider:
    name = os.getenv("ESCALATION_PROVIDER", "stub").lower().strip()
    cls = _PROVIDERS.get(name)

    if cls is None:
        logger.warning("Proveedor desconocido '%s', usando stub", name)
        return StubProvider()

    provider = cls()

    if not provider.is_configured:
        logger.warning(
            "Proveedor '%s' seleccionado pero no configurado — usando stub como fallback",
            name,
        )
        return StubProvider()

    logger.info("Proveedor de escalación activo: %s", name)
    return provider
