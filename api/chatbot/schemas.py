from datetime import datetime
from uuid import UUID

from typing import Optional
from pydantic import BaseModel


class APIMessageParams(BaseModel):
    """
    Request query params with api key and message
    """
    
    message: str
    # conversation_id: Optional[str] = ""


class MessageDataResponse(BaseModel):
    """
    Response model for getting the list with pagination
    """
    # id: UUID
    # conversation_id: UUID
    content: str
    metadata: dict | None = None
    token_usage: dict | None = None
    created_at: datetime
    
