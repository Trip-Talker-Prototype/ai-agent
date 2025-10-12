from datetime import datetime

from api.conversations.models import conversation, message, MessageTypeEnum
from api.conversations.schemas import APIMessageParams, CreateConversationRequest, CreateMessageRequest, MessageDataResponse, ChatModelResponse
from api.conversations.repositories import ConversationRepository, MessageRepository
from api.conversations.entities import ConversationEntities, MessageEntities
from api.chatbot.repositories import ChatBotRepositories

from langchain_openai import OpenAIEmbeddings
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate

from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import RowMapping, select, func, cast, insert, desc
from sqlalchemy.sql.operators import eq
from sqlalchemy.sql import text
from sqlalchemy.exc import ProgrammingError

NOW = datetime.now()

class ChatBotAI:
    def __init__(
            self,
            params: APIMessageParams,
        ):
        self.params = params
        self.llm = OpenAI(temperature = 0)
        self.model = init_chat_model(
            model="gpt-4o-mini",
            stream_usage=True,
        )

    async def language_detection(self) -> str:
        prompt_template = """
You are a language detection model. Your task is to identify the language of the given text.

Identify the language of the following text and respond with the language name only (e.g., English, Spanish, French, etc.):

Text: Halo siapa nama kamu?
Answer: Indonesian

Text: Hello What is your name?
Answer: English

Text: {text}
"""
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["text"]
        )
        formatted_prompt = prompt.format(text=self.params.message)
        response = self.model.invoke(formatted_prompt)

        return response.content.strip()

    async def create_conversation(
            self,
            conn: AsyncConnection,
        ):
        if self.params.conversation_id == "":
            payload = CreateConversationRequest(
                title=self.params.message,
                created_by="user",
            ).transform()
            await ConversationRepository().create_conversation(conn=conn, payload=payload)
            
            
            conversation_id = payload.id
            created_by = payload.created_by
        else:
            data = await ConversationRepository().get_conversation_by_id(
                conn=conn, 
                payload=ConversationEntities(id=self.params.conversation_id)
            )
            if data.get("id", None):
                # get conversation_id and created_by
                conversation_id = data.get("id", "")
                created_by = data.get("created_by", "")
            else:
                # create new conversation_id when conversation_id is not exists
                payload = CreateConversationRequest(
                    title=self.params.message,
                    created_by=created_by
                ).transform()
                await self.__conversation_repo.create_conversation(conn=conn, payload=payload)

                conversation_id = payload.id
                created_by = payload.created_by
        # create message from user
        message_payload = CreateMessageRequest(
            conversation_id=conversation_id,
            content=self.params.message,
            message_type=MessageTypeEnum.question,
            token_usage={},
            created_by=created_by,
            metadata={}
        ).transform()
        await MessageRepository().create_message(conn=conn, payload=message_payload)

        query_embeddings = OpenAIEmbeddings().embed_query(
                self.params.message
            )
            
        results = await ChatBotRepositories().search_similiar_embeddings(
            conn=conn,
            message=query_embeddings
        )
        context = "\n\n".join([doc.document for doc in results])
        prompt_template = """
Anda adalah expert SQL developer yang akan mengkonversi pertanyaan bahasa natural ke SQL query. Kamu akan menggunakan PostgreSQL untuk melakakukan task ini

TANGGAL HARI INI: {current_date}

SCHEMA DATABASE:
{context}

Informasi Terkait Skema:

Table: flight_prices
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
origin_code: kode penanda tempat pemberangkatan
destination_code: kode penanda tempat tujuan

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
5.ketika user bertanya mengenai ketersedian pada tanggal tertentu, gunakan kolom valid_from dengan inputan sesuai dengan jadwal yang diminta user dan valid_to hingga satu bulan kedepan contoh:
- untuk informasi waktu saat ini, gunakan tanggal hari ini yaitu {current_date}
- jika user menyebutkan tanggal saja, gunakan {current_date} sebagai acuan tahun dan bulan
- jika user tidak menyebutkan tanggal, berikan informasi tiket yang valid_from lebih besar atau sama dengan {current_date}
6. Gunakan alias tabel untuk kemudahan baca (contoh: u untuk users, p untuk products, o untuk orders, oi untuk order_items)
7. Return HANYA SQL query tanpa penjelasan tambahan, tanda markdown, atau format lainnya. HANYA berikan SQL query.
8. Berikan Query yang terbaik dan pastikan dapat dijalankan ketika mengeksekusi query. Kamu bisa memberikan detail query supaya dapat memberikan informasi lebih kepada user mengenai apa yang dia cari.
9. HANYA kembalikan SQL query saja tanpa awalan "JAWABAN:" atau teks lainnya
10. Langsung kembalikan query SQL tanpa tambahan apapun

CONTOH QUESTION dan SQL QUERY:
question: Tampilkan semua TIKET
answer: SELECT * FROM flight_prices;

question: Tampilkan tiket dari CGK ke DPS
answer: SELECT fp.flight_number, fp.class, fp.base_price, fp.tax, fp.fee, fp.currency, fp.valid_from, fp.valid_to, fp.origin_code, fp.destination_code, a1.name AS origin_name, a2.name AS destination_name FROM flight_prices fp INNER JOIN airports a1 ON fp.origin_code = a1.code INNER JOIN airports a2 ON fp.destination_code = a2.code WHERE fp.origin_code = 'CGK' AND fp.destination_code = 'DPS';

question: Apakah ada jadwal pesawat dari CGK ke DPS pada tanggal 7 Agustus?
answer: SELECT fp.flight_number, fp.class, fp.base_price, fp.tax, fp.fee, fp.currency, fp.valid_from, fp.valid_to, fp.origin_code, fp.destination_code, a1.name AS origin_name, a2.name AS destination_name FROM flight_prices fp INNER JOIN airports a1 ON fp.origin_code = a1.code INNER JOIN airports a2 ON fp.destination_code = a2.code WHERE fp.origin_code = 'CGK' AND fp.destination_code = 'DPS' AND fp.valid_from >= '2025-08-07' AND valid_to <= '2025-09-07';

question: Apakah ada jadwal pesawat dari Jakarta ke Bali pada tanggal 7 Agustus?
answer: SELECT fp.flight_number, fp.class, fp.base_price, fp.tax, fp.fee, fp.currency, fp.valid_from, fp.valid_to, fp.origin_code, fp.destination_code, a1.name AS origin_name, a2.name AS destination_name FROM flight_prices fp INNER JOIN airports a1 ON fp.origin_code = a1.code INNER JOIN airports a2 ON fp.destination_code = a2.code WHERE a1.city = 'Jakarta' AND a2.city = 'Denpasar' AND fp.valid_from >= '2025-08-07' AND valid_to <= '2025-09-07';

question: {question}
answer:
"""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question", "current_date"]
        )
        
        # Generate SQL using LLM
        formatted_prompt = prompt.format(context=context, question=self.params.message, current_date=NOW.strftime("%Y-%m-%d"))
        sql_query = self.llm(formatted_prompt).strip()
        
        # Clean up the response
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        print("SQL Query :", sql_query)

        try:
            # Execute SQL query
            results = await self.execute_query(conn=conn, sql_query=sql_query)

            # Language Detection
            language = await self.language_detection()

            # Report Agent
            report = await self.report_agent(question=self.params.message, result_query=results, language=language)

            
            ## create message from bot
            message_payload = CreateMessageRequest(
                conversation_id=conversation_id,
                content=report.content,
                message_type=MessageTypeEnum.answer,
                token_usage=report.response_metadata.get("token_usage", {}),
                created_by=created_by,
                metadata={}
            ).transform()
            await MessageRepository().create_message(conn=conn, payload=message_payload)

            # return MessageDataResponse(
            #     content=report.content,
            #     token_usage=report.response_metadata.get("token_usage", {}),
            #     created_at=datetime.now()
            # )

            return MessageDataResponse(content=report.content,token_usage=report.response_metadata.get("token_usage", {}),created_at=datetime.now())
        
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
            formatted_prompt = prompt.format(question=self.params.message, error_message=str_error)
            report = self.model.invoke(formatted_prompt)

            message_payload = CreateMessageRequest(
                conversation_id=conversation_id,
                content=report.content,
                message_type=MessageTypeEnum.answer,
                token_usage=report.response_metadata.get("token_usage", {}),
                created_by=created_by,
                metadata={}
            ).transform()
            await MessageRepository().create_message(conn=conn, payload=message_payload)

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
            language: str,
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
- {language}

OUTPUT:
Return only the final response, no preambles or labels.
"""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["question", "result_query", "language"]
        )
        formatted_prompt = prompt.format(question=question, result_query=result_query, language=language)
        report = self.model.invoke(formatted_prompt)
        return report