from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatStreamRequest(BaseModel):
    message: str = Field(min_length=1)
    car_context: str = Field(min_length=1)
    conversation_id: str = Field(min_length=1)


class LeadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=5, max_length=40)
    car_context: str = Field(min_length=1)
    doubts_summary: str = Field(min_length=1)


class LeadRead(BaseModel):
    id: int
    name: str
    phone: str
    car_context: str
    doubts_summary: str
    status: Literal["NEW", "CALLED"] | str
    created_at: datetime

    model_config = {"from_attributes": True}
