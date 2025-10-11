from typing import Protocol, Sequence

from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import RowMapping

from api.conversations.entities import MessageEntities

class ConversationInterFace(Protocol):
    async def create_conversation(self, conn: AsyncConnection, payload: MessageEntities): ...

class MessageInterFace(Protocol):
    async def create_message(self, conn: AsyncConnection, payload: MessageEntities): ...

    async def get_messages_by_conversation_id(self, conn: AsyncConnection, conversation_id: str) -> Sequence[RowMapping]: ...