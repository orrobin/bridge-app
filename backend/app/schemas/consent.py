import uuid
from datetime import datetime

from pydantic import BaseModel


class ConsentCreateRequest(BaseModel):
    jurisdiction: str
    is_adult_confirmed: bool
    other_party_notice_ack: bool


class ConsentRead(BaseModel):
    id: uuid.UUID
    jurisdiction: str
    is_adult_confirmed: bool
    other_party_notice_ack: bool
    notice_version: str
    consented_at: datetime

    model_config = {"from_attributes": True}
