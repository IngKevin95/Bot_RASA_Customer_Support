from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import messages, sessions, escalate, health

setup_logging()

app = FastAPI(
    title="Customer Support Bot API",
    description="API gateway entre el frontend y el bot de soporte RASA.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(messages.router, prefix="/api/v1", tags=["chat"])
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
app.include_router(escalate.router, prefix="/api/v1", tags=["escalation"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])
