import uuid
from fastapi import APIRouter
from app.models.schemas import SessionResponse, HistoryResponse, BotMessage
from app.services import session_store

router = APIRouter()


@router.post("/sessions", response_model=SessionResponse)
async def create_session():
    session_id = str(uuid.uuid4())
    created_at = session_store.create_session(session_id)
    return SessionResponse(session_id=session_id, created_at=created_at)


@router.get("/sessions/{session_id}/history", response_model=HistoryResponse)
async def get_history(session_id: str):
    messages = session_store.get_history(session_id)
    return HistoryResponse(
        session_id=session_id,
        messages=[
            BotMessage(text=m.text, sender=m.sender, timestamp=m.timestamp)
            for m in messages
        ],
    )
