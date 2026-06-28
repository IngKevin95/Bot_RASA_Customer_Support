import logging
import os

import requests

from .base import EscalationProvider, EscalationResult

logger = logging.getLogger(__name__)

# Genesys Cloud es SaaS — no se despliega on-premise.
# Requiere una org activa con el plan correcto (Communicate, Engage, etc.).
# Docs: https://developer.genesys.cloud/api/rest/v2/


class GenesysProvider(EscalationProvider):
    """
    Escalación via Genesys Cloud Platform API.

    Flujo:
        1. OAuth2 client_credentials → access_token
        2. POST /api/v2/conversations/{conversationId}/participants/{participantId}/transfer
           transfiere la conversación a la cola indicada.

    Variables de entorno requeridas:
        GENESYS_CLIENT_ID      OAuth2 client ID (apps.mypurecloud.com)
        GENESYS_CLIENT_SECRET  OAuth2 client secret
        GENESYS_ORG_ID         Nombre/región de la org (ej: mypurecloud.com)
        GENESYS_QUEUE_ID       ID GUID de la cola de destino (opcional, default: ESCALATION_QUEUE)

    Limitaciones locales:
        - Requiere org real en producción.
        - El token se cachea en memoria por instancia; no es thread-safe si se comparte.
          ponytail: singleton token cache, suficiente para un action server de un proceso.
    """

    _BASE_URLS = {
        "mypurecloud.com": "https://api.mypurecloud.com",
        "mypurecloud.ie": "https://api.mypurecloud.ie",
        "mypurecloud.com.au": "https://api.mypurecloud.com.au",
        "mypurecloud.jp": "https://api.mypurecloud.jp",
        "usw2.pure.cloud": "https://api.usw2.pure.cloud",
        "cac1.pure.cloud": "https://api.cac1.pure.cloud",
        "euw2.pure.cloud": "https://api.euw2.pure.cloud",
        "aps1.pure.cloud": "https://api.aps1.pure.cloud",
    }
    _AUTH_URLS = {
        region: url.replace("api.", "login.")
        for region, url in _BASE_URLS.items()
    }

    def __init__(self) -> None:
        self._client_id = os.getenv("GENESYS_CLIENT_ID", "")
        self._client_secret = os.getenv("GENESYS_CLIENT_SECRET", "")
        self._org_id = os.getenv("GENESYS_ORG_ID", "mypurecloud.com")
        self._queue_id = os.getenv("GENESYS_QUEUE_ID", "")
        self._token: str | None = None

    @property
    def name(self) -> str:
        return "genesys"

    @property
    def is_configured(self) -> bool:
        return bool(self._client_id and self._client_secret)

    @property
    def _api_base(self) -> str:
        return self._BASE_URLS.get(self._org_id, self._BASE_URLS["mypurecloud.com"])

    @property
    def _auth_base(self) -> str:
        return self._AUTH_URLS.get(self._org_id, self._AUTH_URLS["mypurecloud.com"])

    def _get_token(self) -> str | None:
        if self._token:
            return self._token
        try:
            resp = requests.post(
                f"{self._auth_base}/oauth/token",
                data={"grant_type": "client_credentials"},
                auth=(self._client_id, self._client_secret),
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
            logger.warning("[genesys] Credenciales no configuradas — usando stub fallback")
            return EscalationResult(
                success=False,
                provider=self.name,
                message="Genesys Cloud no configurado (faltan GENESYS_CLIENT_ID / GENESYS_CLIENT_SECRET)",
            )

        token = self._get_token()
        if not token:
            return EscalationResult(
                success=False,
                provider=self.name,
                message="No se pudo autenticar contra Genesys Cloud",
            )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # En un flujo real, conversation_id y participant_id vienen del canal de entrada
        # (WebSocket, WebChat, o ACD). Aquí se reciben del context del tracker.
        conversation_id = context.get("genesys_conversation_id", "")
        participant_id = context.get("genesys_participant_id", "")

        if not conversation_id or not participant_id:
            logger.warning(
                "[genesys] Sin conversation_id/participant_id en contexto — "
                "simulando transferencia para demo"
            )
            return EscalationResult(
                success=True,
                provider=self.name,
                message=f"Transferencia a cola '{queue}' registrada (demo — sin conversación activa)",
                ticket_id=f"genesys-demo-{session_id[:8]}",
            )

        queue_id = self._queue_id or queue
        endpoint = (
            f"{self._api_base}/api/v2/conversations/{conversation_id}"
            f"/participants/{participant_id}/replace"
        )
        payload = {
            "queueId": queue_id,
            "userId": None,
            "transfer": {"transferType": "ACD"},
        }

        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            logger.info(
                "[genesys] Transferencia exitosa — conversation=%s queue=%s",
                conversation_id,
                queue_id,
            )
            return EscalationResult(
                success=True,
                provider=self.name,
                message=f"Conversación transferida a cola '{queue}' en Genesys Cloud",
                ticket_id=conversation_id,
            )
        except requests.RequestException as exc:
            logger.error("[genesys] Error en transferencia: %s", exc)
            return EscalationResult(
                success=False,
                provider=self.name,
                message=f"Error al transferir en Genesys: {exc}",
            )
