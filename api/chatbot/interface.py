from typing import Protocol, Sequence
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import RowMapping

class ChatBotInterFace:
    async def search_similiar_embeddings(
        self,
        conn: AsyncConnection, 
        message:list,
        similarity_threshold: float = 0.7,
    ): ...