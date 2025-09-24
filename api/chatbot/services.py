from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_community.llms import OpenAI

from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import text
from sqlalchemy.exc import ProgrammingError

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
        self.model = init_chat_model(
            model="gpt-4o-mini",
            stream_usage=True,
        )

    async def chat(self) -> MessageDataResponse:

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
            Anda adalah expert SQL developer yang akan mengkonversi pertanyaan bahasa natural ke SQL query. Kamu akan menggunakan PostgreSQL untuk melakakukan task ini

            SCHEMA DATABASE:
            {context}

            Informasi Terkait Skema:
    
            Table: flights_prices
            id: ID unik untuk setiap row
            flight_number: nomor penerbangan yang dikombinasikan dengan huruf. contoh GA123
            "class": tipe kelas dari penerbangan tsb
            base_price: harga sebelum dikenakan pajak
            tax: nominal besar pajak
            fee: biaya admin yang dikenakan
            currency: mata uang yang dipakai
            valid_from: waktu awal tersedia 
            valid_to: waktu akhir tersedia atau kadaluarsanya
            created_at: kapan data diubuat
            updated_at: kapan data diubah
            origin: kode penanda tempat pemberangkatan
            destination: kode penanda tempat tujuan

            Table: airports 
            code: kode 3 huruf yang menandakan suatu bandara
            name: nama bandara
            city: kota dimana bandara berada
            country: negara dimana bandara berada
            timezone: waktu setempat bandara
            created_at: data dibuat
            updated_at: data diubah

            ATURAN PENTING:
            1. Gunakan HANYA tabel dan kolom yang ada di schema
            2. Pastikan sintaks PostgreSQL yang benar  
            3. Gunakan JOIN yang tepat untuk relasi antar tabel
            4. Untuk agregasi, gunakan GROUP BY yang sesuai
            5. Gunakan alias tabel untuk kemudahan baca (contoh: u untuk users, p untuk products, o untuk orders, oi untuk order_items)
            6. Return HANYA SQL query tanpa penjelasan tambahan, tanda markdown, atau format lainnya. HANYA berikan SQL query.
            7. Berikan Query yang terbaik dan pastikan dapat dijalankan ketika mengeksekusi query. Kamu bisa memberikan detail query supaya dapat memberikan informasi lebih kepada user mengenai apa yang dia cari.
            8. HANYA kembalikan SQL query saja tanpa awalan "JAWABAN:" atau teks lainnya
            9. Langsung kembalikan query SQL tanpa tambahan apapun

            {question}
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

            try:
                results = await self.execute_query(conn=conn, sql_query=sql_query)

                # Report Agent
                report = await self.report_agent(question=params.message, result_query=results)
                return MessageDataResponse(
                    content=report.content,
                    token_usage=report.response_metadata.get("token_usage", {}),
                    created_at=datetime.now()
                )
            
            except ProgrammingError as e:
                str_error = str(e)

                prompt_template = """
                Kamu adalah data analyst yang ahli yang dimana kamu bekerja untuk suatu pelayanan penerbangan. Kamu akan diberikan suatu error log dan pertanyaan dari user.
                Berikan informasi kepada user mengapa kesalahan dapat terjadi. Bisa jadi user bertanya diluar batas pengetahuanmu.

                contoh:
                question: siapa presiden singapura
                answer: maaf kami tidak mengetahui jawaban mengenai permintaan anda. silahkan bertanya seputar tiket dan penerbangan yang kamu mau tahu ya.

                INSTRUKSI:
                1. JAWAB pertanyaan user secara LANGSUNG. Kamu boleh memodifikasi jawaban dengan lebih natural dan enak dibaca oleh user

                question: {question}
                error message: {error_message}
                """

                prompt = PromptTemplate(
                    template=prompt_template,
                    input_variables=["question", "error_message"]
                )
                formatted_prompt = prompt.format(question=params.message, error_message=str_error)
                report = self.model.invoke(formatted_prompt)

                return MessageDataResponse(
                    content=report.content,
                    token_usage=report.response_metadata.get("token_usage", {}),
                    created_at=datetime.now()
                )
    
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
            
    async def report_agent(
            self,
            question: str,
            result_query: list
    ):
        prompt_template = """
You are a friendly and engaging reporting assistant. 
Your job is to turn the raw result into a smooth, natural, slightly playful explanation that encourages the user to explore further.

USER QUESTION:
{question}

RAW ANSWER / DATA:
{result_query}

TASK:
1. Rewrite the answer in a friendly, conversational tone — as if you are explaining to a friend.
2. Keep all numbers and facts accurate. Do not invent data.
3. Use simple and clear language. Add a little personality to make it feel fun and approachable.
4. If data is empty, respond politely and encourage the user to try asking something else.
5. End your answer with a light, engaging follow-up question that invites the user to continue exploring.

RESPONSE LANGUAGE:
- Must match the language of the user's question.

OUTPUT:
Return only the final response, no preambles or labels.
        """

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["question", "result_query"]
        )
        formatted_prompt = prompt.format(question=question, result_query=result_query)
        report = self.model.invoke(formatted_prompt)
        return report