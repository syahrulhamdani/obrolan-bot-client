import os

from pydantic_settings import BaseSettings


def to_boolean(value: str) -> bool:
    if value.lower() in ["yes", "true", "y", "1"]:
        return True
    return False


class Settings(BaseSettings):
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_USE_BASIC_FORMAT: bool = to_boolean(
        os.getenv("LOG_USE_BASIC_FORMAT", "True")
    )

    CONCURRENCY_LIMIT: int = int(os.getenv("CONCURRENCY_LIMIT", "10"))
    MAX_QUEUE_SIZE: int = int(os.getenv("MAX_QUEUE_SIZE", "5"))

    CHATBOT_URL: str = os.getenv("CHATBOT_URL", "localhost")
    CHATBOT_PORT: int = int(os.getenv("CHATBOT_PORT", "8000"))
    CHATBOT_ENDPOINT: str = os.getenv("CHATBOT_ENDPOINT", "/api")

    FAQ_ENDPOINT: str = os.getenv("FAQ_ENDPOINT", "/api/faq")
    LOGO_PATH: str = os.getenv("LOGO_PATH", "app/assets/deloitte.png")

config = Settings()
