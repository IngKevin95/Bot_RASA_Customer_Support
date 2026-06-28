"""Fixtures compartidas para el suite de tests."""

import pytest
from unittest.mock import MagicMock
from rasa_sdk.executor import CollectingDispatcher


@pytest.fixture
def dispatcher():
    return CollectingDispatcher()


@pytest.fixture
def domain():
    return {}


def make_tracker(slots=None, sender_id="test_user_123"):
    """Crea un Tracker simulado con los slots dados."""
    tracker = MagicMock()
    slots = slots or {}
    tracker.get_slot = lambda key: slots.get(key)
    tracker.sender_id = sender_id
    return tracker
