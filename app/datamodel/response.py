"""Response data model - used for all type of responses."""
from pydantic import BaseModel, Field

from typing import Any


class BaseError(BaseModel):
    code: int
    description: str | None = None


class BaseResponse(BaseModel):
    status: int
    error: BaseError


class ResponseWithSources(BaseModel):
    "A response to the query, with sources."
    response: str = Field(description="Response to the query")
    source: list[str] | None = Field(
        description="List of sources used to answer the question"
    )
    session_id: str = Field(description="Session / Interaction ID")
    message_id: str = Field(description="Response message ID")
