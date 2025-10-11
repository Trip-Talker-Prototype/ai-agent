from uuid import UUID

from pydantic import BaseModel

from api.database.base import AuditBaseModel
from api.conversations.models import MessageTypeEnum


class ConversationEntities(AuditBaseModel):
    id: UUID | None = None
    title: str | None = None
    integration_wizard_id: UUID | None = None
    llm_model_id: UUID | None = None
    created_by: str | None = None

class MessageEntities(AuditBaseModel):
    id: UUID | None = None
    conversation_id: UUID | None = None
    content: str | None = None
    message_type: MessageTypeEnum | None = None
    token_usage: dict | None = None
    created_by: str | None = None
    metadata: dict | None = None

class ConversationsFilter(BaseModel):
    limit: int = 10
    offset: int = 0
    search: str | None = None