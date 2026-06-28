from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

# ponytail: in-memory store, para produccion reemplazar con Redis
_store: dict[str, list["Message"]] = defaultdict(list)
_created: dict[str, datetime] = {}


@dataclass
class Message:
    text: str
    sender: str  # "user" | "bot"
    timestamp: datetime = field(default_factory=datetime.utcnow)


def create_session(session_id: str) -> datetime:
    ts = datetime.utcnow()
    _created[session_id] = ts
    return ts


def get_created_at(session_id: str) -> datetime | None:
    return _created.get(session_id)


def add_message(session_id: str, text: str, sender: str) -> Message:
    msg = Message(text=text, sender=sender)
    _store[session_id].append(msg)
    return msg


def get_history(session_id: str) -> list[Message]:
    return list(_store.get(session_id, []))
