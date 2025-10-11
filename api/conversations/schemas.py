from datetime import datetime
from uuid import UUID

from typing import Optional
from pydantic import BaseModel

from api.conversations.entities import ConversationEntities
from api.conversations.helpers import generate_uuid, generate_time_now
from api.conversations.models import MessageTypeEnum
from api.conversations.entities import MessageEntities


class APIMessageParams(BaseModel):
    """
    Request query params with api key and message
    """
    
    message: str
    conversation_id: Optional[str] = ""
    

class CreateConversationRequest(BaseModel):
    title: str
    created_by: str

    def transform(self):
        return ConversationEntities(
            id=generate_uuid(),
            title=self.title,
            created_by=self.created_by,
        )
    
class CreateMessageRequest(BaseModel):
    conversation_id: UUID
    content: str | None = None
    message_type: MessageTypeEnum
    token_usage: dict
    created_by: str
    metadata: dict | None = None

    def transform(self):
        return MessageEntities(
            id=generate_uuid(),
            conversation_id=self.conversation_id,
            content=self.content,
            message_type=self.message_type,
            token_usage=self.token_usage,
            created_by=self.created_by,
            metadata=self.metadata,
            created_at=generate_time_now()
        )
    
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
    
class ChatModelResponse(BaseModel):
    resp: MessageDataResponse

class ChatModelErrorResponse(BaseModel):
    message: str