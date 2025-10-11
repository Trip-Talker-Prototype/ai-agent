from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import RowMapping, select, func, cast, insert, desc, String
from sqlalchemy.sql.operators import eq

from api.conversations.interface import ConversationInterFace, MessageInterFace
from api.conversations.models import conversation, message, MessageTypeEnum
from api.conversations.entities import ConversationEntities, MessageEntities

class ConversationRepository(ConversationInterFace):
    async def create_conversation(self, conn: AsyncConnection, payload: ConversationEntities):
        stmt = insert(conversation).values(**payload.model_dump(exclude_unset=True)).returning(conversation.c.id)
        try:
            await conn.execute(statement=stmt)
            await conn.commit()
        except Exception as e:
            raise e
        return payload
    
    async def get_conversations(self, conn: AsyncConnection) -> Sequence[RowMapping]:
        stmt = (
            select(conversation)
            .order_by(desc(conversation.c.created_at))
        )
        result = await conn.execute(statement=stmt)
        return result.fetchall()
    
    async def get_conversation_by_id(self, conn: AsyncConnection, payload: ConversationEntities) -> Sequence[RowMapping]:
        messages_cte = (
            select(
                message.c.conversation_id,
                func.jsonb_agg(
                    func.jsonb_build_object(
                        'id', message.c.id,
                        'content', message.c.content,
                        'message_type', cast(message.c.message_type, String),
                        'token_usage', message.c.token_usage,
                        'metadata', message.c.metadata,
                        'created_at', message.c.created_at,
                        'created_by', message.c.created_by
                    )
                ).label('messages')
            )
            .where(eq(message.c.conversation_id, payload.id))
            .group_by(message.c.conversation_id)
            .cte('messages_cte')
        )

        stmt = (
            select(
                conversation,
                messages_cte.c.messages
            )
            .join(messages_cte, conversation.c.id == messages_cte.c.conversation_id)
            .where(eq(conversation.c.id, payload.id))
        )
        try:
            result = await conn.execute(statement=stmt)
            return result.mappings().first()
        except Exception as e:
            raise e
    
class MessageRepository(MessageInterFace):
    async def create_message(self, conn: AsyncConnection, payload: MessageEntities):
        stmt = insert(message).values(**payload.model_dump(exclude_unset=True)).returning(message.c.id)
        try:
            await conn.execute(statement=stmt)
            await conn.commit()
        except Exception as e:
            raise e
        return payload