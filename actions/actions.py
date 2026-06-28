"""
Acciones personalizadas del bot de soporte al cliente.

En produccion, ActionCheckBalance y ActionProcessPayment llamarian
a APIs reales (bancaria, pagos). Aqui usan datos simulados.
"""

import logging
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

logger = logging.getLogger(__name__)

# Datos simulados - en produccion vendrian de una API o DB
MOCK_ACCOUNTS: Dict[str, float] = {
    "1234567": 15000.00,
    "9876543": 8500.50,
    "1111111": 25000.00,
    "4321": 3200.75,
    "7777777": 50000.00,
}


class ActionCheckBalance(Action):
    """Consulta el saldo de una cuenta bancaria."""

    def name(self) -> Text:
        return "action_check_balance"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        account = tracker.get_slot("account_number")

        if not account:
            dispatcher.utter_message(response="utter_ask_account")
            return []

        logger.info("Consultando saldo para cuenta: %s", account)

        balance = MOCK_ACCOUNTS.get(account)

        if balance is not None:
            dispatcher.utter_message(
                text=f"El saldo de tu cuenta {account} es: ${balance:,.2f}"
            )
        else:
            dispatcher.utter_message(
                text=f"No encontre la cuenta {account}. Verifica el numero e intenta de nuevo."
            )

        return [SlotSet("account_number", None)]


class ActionProcessPayment(Action):
    """Procesa un pago o transferencia."""

    def name(self) -> Text:
        return "action_process_payment"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        account = tracker.get_slot("account_number")
        amount_str = tracker.get_slot("amount")

        if not account:
            dispatcher.utter_message(response="utter_ask_account")
            return []

        if not amount_str:
            dispatcher.utter_message(response="utter_ask_amount")
            return []

        try:
            amount = float(amount_str)
        except ValueError:
            dispatcher.utter_message(
                text=f"El monto '{amount_str}' no es valido. Ingresa un numero."
            )
            return []

        if amount <= 0:
            dispatcher.utter_message(
                text="El monto debe ser mayor a cero. Ingresa un valor valido."
            )
            return []

        logger.info("Procesando pago de $%.2f en cuenta %s", amount, account)

        # En produccion: llamada a API de pagos
        # response = payment_api.process(account=account, amount=amount)

        dispatcher.utter_message(
            text=(
                f"Pago procesado exitosamente.\n"
                f"  Cuenta: {account}\n"
                f"  Monto:  ${amount:,.2f}\n"
                f"  Estado: Aprobado"
            )
        )

        return [
            SlotSet("account_number", None),
            SlotSet("amount", None),
        ]


class ActionEscalateAgent(Action):
    """Escala la conversacion a un agente humano (compatible con Genesys)."""

    def name(self) -> Text:
        return "action_escalate_agent"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        logger.info(
            "Escalando a agente humano. Sender: %s", tracker.sender_id
        )

        dispatcher.utter_message(
            text=(
                "Te estoy conectando con un agente humano.\n"
                "Tiempo estimado de espera: 2-3 minutos.\n"
                "Gracias por tu paciencia."
            )
        )

        # En produccion: trigger Genesys Cloud transfer API
        # genesys_client.transfer_conversation(
        #     conversation_id=tracker.sender_id,
        #     queue="soporte_general"
        # )

        return []
