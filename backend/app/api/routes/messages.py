import logging
from fastapi import APIRouter, HTTPException
import httpx

from app.models.schemas import MessageRequest, MessageResponse, BotMessage
from app.services import session_store, rasa_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/messages", response_model=MessageResponse)
async def send_message(req: MessageRequest):
    session_store.add_message(req.session_id, req.message, "user")

    try:
        rasa_responses = await rasa_client.send_message(req.session_id, req.message)
    except httpx.RequestError as exc:
        logger.error("RASA no disponible: %s", exc)
        raise HTTPException(status_code=503, detail="Bot temporalmente no disponible")

    bot_messages = []
    for r in rasa_responses:
        text = r.get("text", "")
        if text:
            msg = session_store.add_message(req.session_id, text, "bot")
            bot_messages.append(BotMessage(text=text, sender="bot", timestamp=msg.timestamp))

    return MessageResponse(session_id=req.session_id, messages=bot_messages)
