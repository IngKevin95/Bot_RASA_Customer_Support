import logging
import requests
from .base import EscalationProvider, EscalationResult
from app.core.config import settings

logger = logging.getLogger(__name__)

_API_BASES = {
    "mypurecloud.com": "https://api.mypurecloud.com",
    "mypurecloud.ie": "https://api.mypurecloud.ie",
    "mypurecloud.com.au": "https://api.mypurecloud.com.au",
    "usw2.pure.cloud": "https://api.usw2.pure.cloud",
}
_AUTH_BASES = {k: v.replace("api.", "login.") for k, v in _API_BASES.items()}


class GenesysProvider(EscalationProvider):
    def __init__(self) -> None:
        self._token: str | None = None

    @property
    def name(self) -> str:
        return "genesys"

    @property
    def is_configured(self) -> bool:
        return bool(settings.GENESYS_CLIENT_ID and settings.GENESYS_CLIENT_SECRET)

    def _api_base(self) -> str:
        return _API_BASES.get(settings.GENESYS_ORG_ID, _API_BASES["mypurecloud.com"])

    def _auth_base(self) -> str:
        return _AUTH_BASES.get(settings.GENESYS_ORG_ID, _AUTH_BASES["mypurecloud.com"])

    def _get_token(self) -> str | None:
        # ponytail: token cache por instancia, sin TTL. Para produccion: renovar antes de expirar.
        if self._token:
            return self._token
        try:
            resp = requests.post(
                f"{self._auth_base()}/oauth/token",
                data={"grant_type": "client_credentials"},
                auth=(settings.GENESYS_CLIENT_ID, settings.GENESYS_CLIENT_SECRET),
                timeout=10,
            )
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
            return self._token
        except requests.RequestException as exc:
            logger.error("[genesys] Error obteniendo token: %s", exc)
            return None

    def escalate(self, session_id: str, queue: str, context: dict) -> EscalationResult:
        if not self.is_configured:
            return EscalationResult(False, self.name, "Genesys no configurado")

        token = self._get_token()
        if not token:
            return EscalationResult(False, self.name, "No se pudo autenticar en Genesys")

        conversation_id = context.get("genesys_conversation_id", "")
        participant_id = context.get("genesys_participant_id", "")

        if not conversation_id or not participant_id:
            logger.warning("[genesys] Sin conversation_id — simulando para demo")
            return EscalationResult(
                True, self.name,
                f"Transferencia a '{queue}' registrada (demo)",
                f"genesys-demo-{session_id[:8]}",
            )

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        queue_id = settings.GENESYS_QUEUE_ID or queue
        try:
            resp = requests.post(
                f"{self._api_base()}/api/v2/conversations/{conversation_id}"
                f"/participants/{participant_id}/replace",
                json={"queueId": queue_id, "userId": None, "transfer": {"transferType": "ACD"}},
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            return EscalationResult(True, self.name, f"Transferido a '{queue}'", conversation_id)
        except requests.RequestException as exc:
            logger.error("[genesys] Error: %s", exc)
            return EscalationResult(False, self.name, str(exc))
