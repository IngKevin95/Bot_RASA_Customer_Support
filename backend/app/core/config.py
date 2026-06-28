from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    RASA_URL: str = "http://localhost:5005"
    ESCALATION_PROVIDER: str = "stub"
    ESCALATION_QUEUE: str = "soporte_general"
    CORS_ORIGINS: list[str] = ["http://localhost", "http://localhost:8080", "http://localhost:80"]
    LOG_LEVEL: str = "INFO"
    SESSION_TTL_MINUTES: int = 60

    # Chatwoot
    CHATWOOT_URL: str = ""
    CHATWOOT_API_TOKEN: str = ""
    CHATWOOT_ACCOUNT_ID: str = ""
    CHATWOOT_INBOX_ID: str = ""

    # Genesys
    GENESYS_CLIENT_ID: str = ""
    GENESYS_CLIENT_SECRET: str = ""
    GENESYS_ORG_ID: str = "mypurecloud.com"
    GENESYS_QUEUE_ID: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
