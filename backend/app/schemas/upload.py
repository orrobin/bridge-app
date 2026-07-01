import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChatUploadRequest(BaseModel):
    raw_text: str = Field(min_length=1)
    thread_label: str | None = None


class RedactedTurn(BaseModel):
    speaker: str
    text: str


class ChatUploadResponse(BaseModel):
    id: uuid.UUID
    thread_id: uuid.UUID
    turns: list[RedactedTurn]
    expires_at: datetime
