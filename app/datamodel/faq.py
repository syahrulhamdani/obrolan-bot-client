from pydantic import BaseModel, Field


class FAQPayload(BaseModel):
    """Payload to generate FAQ."""
    date: str


class FAQItem(BaseModel):
    """FAQ item data model."""
    topic: str
    question: str
    answer: str


class FAQ(BaseModel):
    """FAQ data model."""
    faq: list[FAQItem]
    total_item: int
