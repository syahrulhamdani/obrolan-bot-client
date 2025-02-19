from pydantic import BaseModel, Field


class ChatQuery(BaseModel):
    query: str
    session_id: str
    persona: str
    user_id: str | None = Field(default=None)
    language: str | None = Field(default=None)
