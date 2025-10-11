import uuid
from enum import StrEnum

from sqlalchemy import Table, Column, String, Numeric, Date, UUID, ForeignKey, ForeignKeyConstraint, Text, Enum
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.sql import func

from api.models.base import get_audit_columns
from api.database.client import metadata

class MessageTypeEnum(StrEnum):
    question = "question"
    answer = "answer"

conversation = Table(
    "conversations",
    metadata,
    Column("id", UUID, primary_key=True, default=uuid.uuid4),
    Column("title", String, nullable=False),
    *get_audit_columns(),
)

message = Table(
    "messages",
    metadata,
    Column("id", UUID, primary_key=True, default=uuid.uuid4),
    Column("conversation_id", UUID, nullable=False),
    Column("content", Text, nullable=False),
    Column("message_type", Enum(MessageTypeEnum), nullable=False),
    Column("token_usage", JSONB, nullable=True),
    Column("metadata", JSONB, nullable=True),
    ForeignKeyConstraint(
        name="fk_message_conversation", columns=["conversation_id"], refcolumns=["conversation.id"]
    ),
    *get_audit_columns(),
)
