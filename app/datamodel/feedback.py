from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class Feedback(BaseModel):
    """Feedback data model."""
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    interaction_id: str
    ai_response_id: str
    feedback_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str | None = Field(default=str())
    use_case: str
    rating: int
    input_query: str
    response: str | None = Field(default=str())
    feedback_detail: str | None = Field(default=str())
