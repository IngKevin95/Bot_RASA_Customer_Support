import logging
import os

import requests

from .base import EscalationProvider, EscalationResult

logger = logging.getLogger(__name__)


class ChatwootProvider(EscalationProvider):
    """
    Escalación via Chatwoot — crea una nueva conversación en la bandeja de entrada
    configurada y la asigna a la cola indicada.

    Variables de entorno requeridas:
        CHATWOOT_URL         URL base de la instancia (ej: http://localhost:3000)
        CHATWOOT_API_TOKEN   User access token (Settings > Access Token en Chatwoot)
        CHATWOOT_ACCOUNT_ID  ID numérico de la cuenta
        CHATWOOT_INBOX_ID    ID numérico del inbox donde se crea la conversación
    """

    def __init__(self) -> None:
        self._url = os.getenv("CHATWOOT_URL", "").rstrip("/")
        self._token = os.getenv("CHATWOOT_API_TOKEN", "")
        self._account_id = os.getenv("CHATWOOT_ACCOUNT_ID", "")
        self._inbox_id = os.getenv("CHATWOOT_INBOX_ID", "")

    @property
    def name(self) -> str:
        return "chatwoot"

    @property
    def is_configured(self) -> bool:
        return all([self._url, self._token, self._account_id, self._inbox_id])

    def escalate(self, session_id: str, queue: str, context: dict) -> EscalationResult:
        if not self.is_configured:
            logger.warning("[chatwoot] Variables de entorno incompletas — usando stub")
            return EscalationResult(
                success=False,
                provider=self.name,
                message="Chatwoot no configurado (faltan variables de entorno)",
            )

        headers = {
            "api_access_token": self._token,
            "Content-Type": "application/json",
        }

        # 1. Crear o buscar contacto para esta sesión
        contact_id = self._get_or_create_contact(session_id, headers)
        if contact_id is None:
            return EscalationResult(
                success=False,
                provider=self.name,
                message="No se pudo crear el contacto en Chatwoot",
            )

        # 2. Crear conversación
        endpoint = f"{self._url}/api/v1/accounts/{self._account_id}/conversations"
        payload = {
            "inbox_id": int(self._inbox_id),
            "contact_id": contact_id,
            "additional_attributes": {
                "rasa_session_id": session_id,
                "escalation_queue": queue,
            },
        }

        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            ticket_id = str(data.get("id", ""))
            logger.info("[chatwoot] Conversación creada — id=%s session=%s", ticket_id, session_id)
            return EscalationResult(
                success=True,
                provider=self.name,
                message=f"Conversación abierta en Chatwoot (id={ticket_id})",
                ticket_id=ticket_id,
            )
        except requests.RequestException as exc:
            logger.error("[chatwoot] Error al crear conversación: %s", exc)
            return EscalationResult(
                success=False,
                provider=self.name,
                message=f"Error al contactar Chatwoot: {exc}",
            )

    def _get_or_create_contact(self, session_id: str, headers: dict) -> int | None:
        endpoint = f"{self._url}/api/v1/accounts/{self._account_id}/contacts"
        try:
            resp = requests.post(
                endpoint,
                json={"name": f"Bot User {session_id[:8]}", "identifier": session_id},
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("id")
        except requests.RequestException as exc:
            logger.error("[chatwoot] Error al crear contacto: %s", exc)
            return None
