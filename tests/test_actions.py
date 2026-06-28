"""
Tests unitarios para las custom actions del bot de soporte.

Correr con: pytest tests/test_actions.py -v
O con cobertura: pytest tests/test_actions.py --cov=actions --cov-report=term-missing
"""

import pytest
from unittest.mock import MagicMock, patch
from rasa_sdk.events import SlotSet

from actions.actions import (
    ActionCheckBalance,
    ActionProcessPayment,
    ActionEscalateAgent,
    MOCK_ACCOUNTS,
)
from actions.providers.base import EscalationResult
from tests.conftest import make_tracker


class TestActionCheckBalance:
    """Tests para action_check_balance."""

    def test_cuenta_valida_retorna_saldo(self, dispatcher, domain):
        tracker = make_tracker({"account_number": "1234567"})
        events = ActionCheckBalance().run(dispatcher, tracker, domain)

        mensajes = " ".join(m.get("text", "") for m in dispatcher.messages)
        assert "1234567" in mensajes
        assert "15,000.00" in mensajes
        assert SlotSet("account_number", None) in events

    def test_cuenta_inexistente_retorna_mensaje_error(self, dispatcher, domain):
        tracker = make_tracker({"account_number": "0000000"})
        events = ActionCheckBalance().run(dispatcher, tracker, domain)

        mensajes = " ".join(m.get("text", "") for m in dispatcher.messages)
        assert "No encontre" in mensajes
        assert "0000000" in mensajes
        assert SlotSet("account_number", None) in events

    def test_sin_cuenta_solicita_numero(self, dispatcher, domain):
        tracker = make_tracker({"account_number": None})
        events = ActionCheckBalance().run(dispatcher, tracker, domain)

        responses = [m.get("response", "") for m in dispatcher.messages]
        assert "utter_ask_account" in responses
        assert events == []

    @pytest.mark.parametrize("account,expected_balance", [
        ("1234567", "15,000.00"),
        ("9876543", "8,500.50"),
        ("1111111", "25,000.00"),
        ("7777777", "50,000.00"),
    ])
    def test_cuentas_conocidas_retornan_saldo_correcto(
        self, dispatcher, domain, account, expected_balance
    ):
        tracker = make_tracker({"account_number": account})
        ActionCheckBalance().run(dispatcher, tracker, domain)

        mensajes = " ".join(m.get("text", "") for m in dispatcher.messages)
        assert account in mensajes
        assert expected_balance in mensajes

    def test_nombre_accion_correcto(self):
        assert ActionCheckBalance().name() == "action_check_balance"


class TestActionProcessPayment:
    """Tests para action_process_payment."""

    def test_pago_valido_retorna_confirmacion(self, dispatcher, domain):
        tracker = make_tracker({"account_number": "1234567", "amount": "500"})
        events = ActionProcessPayment().run(dispatcher, tracker, domain)

        mensajes = " ".join(m.get("text", "") for m in dispatcher.messages)
        assert "Pago procesado" in mensajes
        assert "500" in mensajes
        assert "Aprobado" in mensajes
        assert SlotSet("account_number", None) in events
        assert SlotSet("amount", None) in events

    def test_pago_con_monto_decimal(self, dispatcher, domain):
        tracker = make_tracker({"account_number": "9876543", "amount": "1500.75"})
        events = ActionProcessPayment().run(dispatcher, tracker, domain)

        mensajes = " ".join(m.get("text", "") for m in dispatcher.messages)
        assert "Aprobado" in mensajes
        assert SlotSet("amount", None) in events

    def test_sin_cuenta_solicita_cuenta(self, dispatcher, domain):
        tracker = make_tracker({"account_number": None, "amount": "100"})
        events = ActionProcessPayment().run(dispatcher, tracker, domain)

        responses = [m.get("response", "") for m in dispatcher.messages]
        assert "utter_ask_account" in responses
        assert events == []

    def test_sin_monto_solicita_monto(self, dispatcher, domain):
        tracker = make_tracker({"account_number": "1234567", "amount": None})
        events = ActionProcessPayment().run(dispatcher, tracker, domain)

        responses = [m.get("response", "") for m in dispatcher.messages]
        assert "utter_ask_amount" in responses
        assert events == []

    def test_monto_no_numerico_retorna_error(self, dispatcher, domain):
        tracker = make_tracker({"account_number": "1234567", "amount": "doscientos"})
        events = ActionProcessPayment().run(dispatcher, tracker, domain)

        mensajes = " ".join(m.get("text", "") for m in dispatcher.messages)
        assert "doscientos" in mensajes
        assert "valido" in mensajes
        assert events == []

    @pytest.mark.parametrize("monto_invalido", ["-50", "-0.01", "0", "0.0"])
    def test_monto_no_positivo_rechazado(self, dispatcher, domain, monto_invalido):
        tracker = make_tracker({"account_number": "1234567", "amount": monto_invalido})
        events = ActionProcessPayment().run(dispatcher, tracker, domain)

        mensajes = " ".join(m.get("text", "") for m in dispatcher.messages)
        assert "mayor a cero" in mensajes
        assert events == []

    def test_nombre_accion_correcto(self):
        assert ActionProcessPayment().name() == "action_process_payment"


class TestActionEscalateAgent:
    """Tests para action_escalate_agent."""

    def _mock_provider(self, success=True):
        provider = MagicMock()
        provider.escalate.return_value = EscalationResult(
            success=success,
            provider="stub",
            message="ok" if success else "error",
            ticket_id="test-001" if success else None,
        )
        return provider

    def test_escalado_retorna_mensaje_confirmacion(self, dispatcher, domain):
        tracker = make_tracker(sender_id="session_abc_123")
        with patch("actions.actions.get_provider", return_value=self._mock_provider()):
            events = ActionEscalateAgent().run(dispatcher, tracker, domain)

        mensajes = " ".join(m.get("text", "") for m in dispatcher.messages)
        assert "agente humano" in mensajes
        assert events == []

    def test_mensaje_incluye_tiempo_espera(self, dispatcher, domain):
        tracker = make_tracker()
        with patch("actions.actions.get_provider", return_value=self._mock_provider()):
            ActionEscalateAgent().run(dispatcher, tracker, domain)

        mensajes = " ".join(m.get("text", "") for m in dispatcher.messages)
        assert "minuto" in mensajes

    def test_escalado_llama_al_provider(self, dispatcher, domain):
        tracker = make_tracker(sender_id="sesion_test")
        mock_provider = self._mock_provider()
        with patch("actions.actions.get_provider", return_value=mock_provider):
            ActionEscalateAgent().run(dispatcher, tracker, domain)

        mock_provider.escalate.assert_called_once()
        call_args = mock_provider.escalate.call_args
        assert call_args.kwargs["session_id"] == "sesion_test"

    def test_escalado_no_modifica_slots(self, dispatcher, domain):
        tracker = make_tracker({"account_number": "1234567"})
        with patch("actions.actions.get_provider", return_value=self._mock_provider()):
            events = ActionEscalateAgent().run(dispatcher, tracker, domain)

        slot_events = [e for e in events if isinstance(e, dict) and e.get("event") == "slot"]
        assert slot_events == []

    def test_escalado_falla_silenciosamente(self, dispatcher, domain):
        """Si el provider falla, el bot igual responde al usuario."""
        tracker = make_tracker()
        with patch("actions.actions.get_provider", return_value=self._mock_provider(success=False)):
            events = ActionEscalateAgent().run(dispatcher, tracker, domain)

        mensajes = " ".join(m.get("text", "") for m in dispatcher.messages)
        assert "agente humano" in mensajes
        assert events == []

    def test_nombre_accion_correcto(self):
        assert ActionEscalateAgent().name() == "action_escalate_agent"
