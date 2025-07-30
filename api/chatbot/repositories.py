from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import RowMapping, select, func, cast, insert, desc
from sqlalchemy.sql.operators import eq

from api.chatbot.interface import ChatBotInterFace
from api.langchain_pg.models import langchain_pg_embedding
# from api.flights.models import flight_price

class ChatBotRepositories(ChatBotInterFace):
    async def search_similiar_embeddings(
        self,
        conn: AsyncConnection, 
        message:list,
        similarity_threshold: float = 0.7,
        limit: int = 10
    ):
        stmt = select(
            langchain_pg_embedding.c.embedding,
            langchain_pg_embedding.c.document,
            (1 - langchain_pg_embedding.c.embedding.cosine_distance(message)).label('similarity_score')
        )
        # .where(
        #     eq(flight_price.c.integration_wizard_id,flight_price),
        # )

        query = stmt.order_by(desc('similarity_score')).limit(limit)
        try:
            # Execute data query
            data_result = await conn.execute(statement=stmt)
            data = data_result.mappings().fetchall()

            return data
        except Exception as e:
            raise e