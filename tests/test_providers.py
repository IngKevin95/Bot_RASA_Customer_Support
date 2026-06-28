"""
Tests unitarios para el módulo de escalation providers.

Correr con: pytest tests/test_providers.py -v
"""

import os
import pytest
from unittest.mock import patch

from actions.providers.base import EscalationProvider, EscalationResult
from actions.providers.stub import StubProvider
from actions.providers.factory import get_provider


class TestStubProvider:
    def test_name(self):
        assert StubProvider().name == "stub"

    def test_is_configured(self):
        assert StubProvider().is_configured is True

    def test_escalate_retorna_success(self):
        result = StubProvider().escalate(
            session_id="ses-123", queue="soporte", context={}
        )
        assert isinstance(result, EscalationResult)
        assert result.success is True
        assert result.provider == "stub"
        assert result.ticket_id is not None
        assert "ses-123"[:8] in result.ticket_id

    def test_escalate_incluye_session_en_ticket(self):
        result = StubProvider().escalate(
            session_id="abcdefgh_extra", queue="q", context={}
        )
        assert result.ticket_id == "stub-abcdefgh"


class TestEscalationBase:
    def test_is_configured_default_true(self):
        # La implementación base devuelve True
        assert StubProvider().is_configured is True


class TestGetProvider:
    def test_default_es_stub(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ESCALATION_PROVIDER", None)
            provider = get_provider()
        assert isinstance(provider, StubProvider)

    def test_env_stub_retorna_stub(self):
        with patch.dict(os.environ, {"ESCALATION_PROVIDER": "stub"}):
            provider = get_provider()
        assert isinstance(provider, StubProvider)

    def test_env_desconocido_fallback_a_stub(self):
        with patch.dict(os.environ, {"ESCALATION_PROVIDER": "inexistente"}):
            provider = get_provider()
        assert isinstance(provider, StubProvider)

    def test_env_mayusculas_funciona(self):
        with patch.dict(os.environ, {"ESCALATION_PROVIDER": "STUB"}):
            provider = get_provider()
        assert isinstance(provider, StubProvider)

    def test_provider_no_configurado_fallback_a_stub(self):
        # ChatwootProvider sin variables de entorno no está configurado → debe caer a stub
        with patch.dict(os.environ, {"ESCALATION_PROVIDER": "chatwoot"}, clear=False):
            for var in ("CHATWOOT_URL", "CHATWOOT_API_TOKEN", "CHATWOOT_ACCOUNT_ID", "CHATWOOT_INBOX_ID"):
                os.environ.pop(var, None)
            provider = get_provider()
        assert isinstance(provider, StubProvider)

    def test_chatwoot_configurado_retorna_chatwoot(self):
        from actions.providers.chatwoot import ChatwootProvider
        env = {
            "ESCALATION_PROVIDER": "chatwoot",
            "CHATWOOT_URL": "http://localhost:3000",
            "CHATWOOT_API_TOKEN": "tok123",
            "CHATWOOT_ACCOUNT_ID": "1",
            "CHATWOOT_INBOX_ID": "2",
        }
        with patch.dict(os.environ, env):
            provider = get_provider()
        assert isinstance(provider, ChatwootProvider)
