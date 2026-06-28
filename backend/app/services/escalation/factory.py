import logging
from app.core.config import settings
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
    name = settings.ESCALATION_PROVIDER.lower().strip()
    cls = _PROVIDERS.get(name)

    if cls is None:
        logger.warning("Proveedor desconocido '%s', usando stub", name)
        return StubProvider()

    provider = cls()
    if not provider.is_configured:
        logger.warning("Proveedor '%s' sin configurar — fallback a stub", name)
        return StubProvider()

    logger.info("Proveedor activo: %s", name)
    return provider
