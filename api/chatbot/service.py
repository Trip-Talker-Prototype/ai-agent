from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_community.llms import OpenAI

from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import text

from api.chatbot.schemas import APIMessageParams, MessageDataResponse
from api.chatbot.repositories import ChatBotRepositories
from api.database.client import engine

class ChatBotAI:
    def __init__(
            self, 
            params: APIMessageParams
        ):
        self.prompt = params.message
        self.llm = OpenAI(temperature = 0)

    async def chat(self) -> MessageDataResponse:
        self.model = init_chat_model(
            model="gpt-4o-mini",
            stream_usage=True,
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Provide a clear, in-depth, and easy-to-understand answer to the following question"),
            ("human", "{user_input}")
        ])

        llm_chain = prompt | self.model
        complete_response = await llm_chain.ainvoke({"user_input": self.prompt})
        res = MessageDataResponse(
            content=complete_response.content,
            token_usage=complete_response.response_metadata.get("token_usage", {}),
            created_at=datetime.now()
        )
        return res

    async def chat_v2(
            self,
            conn: AsyncConnection,
            params: APIMessageParams,
    ) -> MessageDataResponse:
        # try:
            query_embeddings = OpenAIEmbeddings().embed_query(
                params.message
            )
            
            results = await ChatBotRepositories().search_similiar_embeddings(
                conn=conn,
                message=query_embeddings
            )

            context = "\n\n".join([doc.document for doc in results])
            prompt_template = """
        Anda adalah expert SQL developer yang akan mengkonversi pertanyaan bahasa natural ke SQL query.

        SCHEMA DATABASE:
        {context}

        ATURAN PENTING:
        1. Gunakan HANYA tabel dan kolom yang ada di schema
        2. Pastikan sintaks PostgreSQL yang benar
        3. Gunakan JOIN yang tepat untuk relasi antar tabel
        4. Untuk agregasi, gunakan GROUP BY yang sesuai
        5. Return HANYA SQL query, tanpa penjelasan tambahan
        6. Gunakan alias tabel untuk kemudahan baca (u untuk users, p untuk products, o untuk orders, oi untuk order_items)

        CONTOH FORMAT QUERY:
        - SELECT query: SELECT kolom FROM tabel WHERE kondisi;
        - JOIN query: SELECT u.name, COUNT(o.order_id) FROM users u LEFT JOIN orders o ON u.user_id = o.user_id GROUP BY u.user_id, u.name;

        PERTANYAAN: {question}

        SQL QUERY:
        """

            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )
            
            # Generate SQL using LLM
            formatted_prompt = prompt.format(context=context, question=params.message)
            sql_query = self.llm(formatted_prompt).strip()
            
            # Clean up the response
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            
            print("SQL Query :", sql_query)
            results = await self.execute_query(conn=conn, sql_query=sql_query)
            return results
    
    async def execute_query(
            self,
            conn: AsyncConnection,
            sql_query: str
        ):
            try:
                # Execute paginated query
                result = await conn.execute(text(sql_query))
                return result.mappings().fetchall()
            except Exception as e:
                raise e