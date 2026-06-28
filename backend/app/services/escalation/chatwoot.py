import logging
import requests
from .base import EscalationProvider, EscalationResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class ChatwootProvider(EscalationProvider):
    @property
    def name(self) -> str:
        return "chatwoot"

    @property
    def is_configured(self) -> bool:
        return all([
            settings.CHATWOOT_URL,
            settings.CHATWOOT_API_TOKEN,
            settings.CHATWOOT_ACCOUNT_ID,
            settings.CHATWOOT_INBOX_ID,
        ])

    def escalate(self, session_id: str, queue: str, context: dict) -> EscalationResult:
        if not self.is_configured:
            return EscalationResult(False, self.name, "Chatwoot no configurado")

        headers = {
            "api_access_token": settings.CHATWOOT_API_TOKEN,
            "Content-Type": "application/json",
        }
        base = settings.CHATWOOT_URL.rstrip("/")
        account_id = settings.CHATWOOT_ACCOUNT_ID

        contact_id = self._get_or_create_contact(session_id, headers, base, account_id)
        if contact_id is None:
            return EscalationResult(False, self.name, "No se pudo crear el contacto")

        try:
            resp = requests.post(
                f"{base}/api/v1/accounts/{account_id}/conversations",
                json={
                    "inbox_id": int(settings.CHATWOOT_INBOX_ID),
                    "contact_id": contact_id,
                    "additional_attributes": {"rasa_session_id": session_id, "queue": queue},
                },
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            ticket_id = str(resp.json().get("id", ""))
            logger.info("[chatwoot] Conversacion creada id=%s", ticket_id)
            return EscalationResult(True, self.name, f"Conversacion abierta (id={ticket_id})", ticket_id)
        except requests.RequestException as exc:
            logger.error("[chatwoot] Error: %s", exc)
            return EscalationResult(False, self.name, str(exc))

    def _get_or_create_contact(self, session_id, headers, base, account_id) -> int | None:
        try:
            resp = requests.post(
                f"{base}/api/v1/accounts/{account_id}/contacts",
                json={"name": f"Bot User {session_id[:8]}", "identifier": session_id},
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("id")
        except requests.RequestException as exc:
            logger.error("[chatwoot] Error creando contacto: %s", exc)
            return None
