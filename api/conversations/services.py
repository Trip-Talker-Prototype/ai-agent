from datetime import datetime

from api.conversations.models import conversation, message, MessageTypeEnum
from api.conversations.schemas import APIMessageParams, CreateConversationRequest, CreateMessageRequest, MessageDataResponse, ChatModelResponse
from api.conversations.repositories import ConversationRepository, MessageRepository, InMemoryChatMessageHistory
from api.conversations.entities import ConversationEntities, MessageEntities
from api.chatbot.repositories import ChatBotRepositories

from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser

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
        self.conversation_id = ""

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

    async def clean_sql(self, sql_output: str):
        sql_output = sql_output.replace("\\n", "\n").replace("\\t", "\t")
    
        # Remove common prefixes (case insensitive)
        prefixes_to_remove = [
            "answer:", "sql:", "query:", "result:", 
            "here is the sql:", "the query is:",
            "```sql", "```", "A:", "AI:", "System:"
        ]
        
        sql_lower = sql_output.lower().strip()
        for prefix in prefixes_to_remove:
            if sql_lower.startswith(prefix):
                sql_output = sql_output[len(prefix):].strip()
                sql_lower = sql_output.lower().strip()
        
        # Remove trailing markdown
        if sql_output.endswith("```"):
            sql_output = sql_output[:-3].strip()
        
        # Remove multiple newlines at start
        sql_output = sql_output.lstrip("\n").strip()
        
        # Ensure it starts with a SQL keyword
        sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH"]
        if not any(sql_output.upper().startswith(kw) for kw in sql_keywords):
            # Try to find the SQL part
            for keyword in sql_keywords:
                if keyword in sql_output.upper():
                    idx = sql_output.upper().index(keyword)
                    sql_output = sql_output[idx:].strip()
                    break
        
        return sql_output

    def validate_sql_output(self, sql: str) -> bool:
        """Validasi apakah output benar-benar SQL query"""
        
        sql_upper = sql.upper().strip()
        
        # Must start with SQL keyword
        valid_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH"]
        if not any(sql_upper.startswith(kw) for kw in valid_keywords):
            print(f"❌ Invalid SQL: doesn't start with SQL keyword")
            return False
        
        # Should not contain conversational words
        conversational_words = ["AI:", "ASSISTANT:", "JAWABAN:", "TIKET PALING MAHAL ADALAH"]
        for word in conversational_words:
            if word in sql_upper:
                print(f"❌ Invalid SQL: contains conversational text '{word}'")
                return False
        
        return True

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
            
            
            self.conversation_id = payload.id
            created_by = payload.created_by
        else:
            data = await ConversationRepository().get_conversation_by_id(
                conn=conn, 
                payload=ConversationEntities(id=self.params.conversation_id)
            )
            if data.get("id", None):
                # get conversation_id and created_by

                self.conversation_id = self.params.conversation_id
                conversation_id = data.get("id", "")
                created_by = data.get("created_by", "")
            else:
                # create new conversation_id when conversation_id is not exists
                payload = CreateConversationRequest(
                    title=self.params.message,
                    created_by=created_by
                ).transform()
                await self.__conversation_repo.create_conversation(conn=conn, payload=payload)

                self.conversation_id = self.params.conversation_id
                conversation_id = payload.id
                created_by = payload.created_by
        
        # create message from user
        message_payload = CreateMessageRequest(
            conversation_id=self.conversation_id,
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
#         prompt_template = """
# Anda adalah expert SQL developer yang akan mengkonversi pertanyaan bahasa natural ke SQL query. Kamu akan menggunakan PostgreSQL untuk melakakukan task ini

# TANGGAL HARI INI: {current_date}

# SCHEMA DATABASE:
# {context}

# Informasi Terkait Skema:

# Table: flight_prices
# id: ID unik untuk setiap row
# flight_number: nomor penerbangan yang dikombinasikan dengan huruf. contoh GA123
# "class": tipe kelas dari penerbangan tsb
# base_price: harga sebelum dikenakan pajak
# tax: nominal besar pajak
# fee: biaya admin yang dikenakan
# currency: mata uang yang dipakai
# valid_from: waktu awal tersedia 
# valid_to: waktu akhir tersedia atau kadaluarsanya
# created_at: kapan data diubuat
# updated_at: kapan data diubah
# origin_code: kode penanda tempat pemberangkatan
# destination_code: kode penanda tempat tujuan

# Table: airports 
# code: kode 3 huruf yang menandakan suatu bandara
# name: nama bandara
# city: kota dimana bandara berada
# country: negara dimana bandara berada
# timezone: waktu setempat bandara
# created_at: data dibuat
# updated_at: data diubah

# ATURAN PENTING:
# 1. Gunakan HANYA tabel dan kolom yang ada di schema
# 2. Pastikan sintaks PostgreSQL yang benar  
# 3. Gunakan JOIN yang tepat untuk relasi antar tabel
# 4. Untuk agregasi, gunakan GROUP BY yang sesuai
# 5.ketika user bertanya mengenai ketersedian pada tanggal tertentu, gunakan kolom valid_from dengan inputan sesuai dengan jadwal yang diminta user dan valid_to hingga satu bulan kedepan contoh:
# - untuk informasi waktu saat ini, gunakan tanggal hari ini yaitu {current_date}
# - jika user menyebutkan tanggal saja, gunakan {current_date} sebagai acuan tahun dan bulan
# - jika user tidak menyebutkan tanggal, berikan informasi tiket yang valid_from lebih besar atau sama dengan {current_date}
# 6. Gunakan alias tabel untuk kemudahan baca (contoh: u untuk users, p untuk products, o untuk orders, oi untuk order_items)
# 7. Return HANYA SQL query tanpa penjelasan tambahan, tanda markdown, tanpa awalan "JAWABAN:", "answer:", "query:", "sql:", etc. HANYA BERIKAN RAW QUERY.
# 8. Berikan Query yang terbaik dan pastikan dapat dijalankan ketika mengeksekusi query. Kamu bisa memberikan detail query supaya dapat memberikan informasi lebih kepada user mengenai apa yang dia cari.

# EXAMPLES:
# Q: Tampilkan semua TIKET
# A: SELECT * FROM flight_prices;

# Q: Tampilkan tiket dari CGK ke DPS
# A: SELECT fp.flight_number, fp.class, fp.base_price, fp.tax, fp.fee, fp.currency, fp.valid_from, fp.valid_to, fp.origin_code, fp.destination_code, a1.name AS origin_name, a2.name AS destination_name FROM flight_prices fp INNER JOIN airports a1 ON fp.origin_code = a1.code INNER JOIN airports a2 ON fp.destination_code = a2.code WHERE fp.origin_code = 'CGK' AND fp.destination_code = 'DPS';

# Q: Apakah ada jadwal pesawat dari CGK ke DPS pada tanggal 7 Agustus?
# A: SELECT fp.flight_number, fp.class, fp.base_price, fp.tax, fp.fee, fp.currency, fp.valid_from, fp.valid_to, fp.origin_code, fp.destination_code, a1.name AS origin_name, a2.name AS destination_name FROM flight_prices fp INNER JOIN airports a1 ON fp.origin_code = a1.code INNER JOIN airports a2 ON fp.destination_code = a2.code WHERE fp.origin_code = 'CGK' AND fp.destination_code = 'DPS' AND fp.valid_from >= '2025-08-07' AND valid_to <= '2025-09-07';

# Q: Apakah ada jadwal pesawat dari Jakarta ke Bali pada tanggal 7 Agustus?
# A: SELECT fp.flight_number, fp.class, fp.base_price, fp.tax, fp.fee, fp.currency, fp.valid_from, fp.valid_to, fp.origin_code, fp.destination_code, a1.name AS origin_name, a2.name AS destination_name FROM flight_prices fp INNER JOIN airports a1 ON fp.origin_code = a1.code INNER JOIN airports a2 ON fp.destination_code = a2.code WHERE a1.city = 'Jakarta' AND a2.city = 'Denpasar' AND fp.valid_from >= '2025-08-07' AND valid_to <= '2025-09-07';

# Now generate SQL for the user's question below.
# """

        understanding_prompt = """
Kamu adalah SQL analyst assistant. Tugasmu adalah memahami pertanyaan user dan context sebelumnya.

TANGGAL HARI INI: {current_date}

DATABASE SCHEMA:
{context}

INFORMASI TABEL:
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

Tugasmu:
1. Jika user bertanya follow-up (seperti "yang paling murah?", "berapa harganya?"), identifikasi apa yang dimaksud dari percakapan sebelumnya
2. Reformulasi pertanyaan menjadi pertanyaan lengkap yang bisa dijawab dengan SQL
3. Output harus dalam format: "QUERY_INTENT: [penjelasan singkat apa yang harus di-query]"

Contoh:
User sebelumnya tanya: "Ada penerbangan Jakarta-Bali tanggal 7 Agustus?"
User sekarang tanya: "Yang paling murah?"
Output: "QUERY_INTENT: Cari penerbangan Jakarta-Bali tanggal 7 Agustus dengan harga paling murah"
"""

        sql_prompt = """
Kamu adalah expert SQL generator. Generate ONLY valid PostgreSQL query.

DATABASE SCHEMA:
{context}

ATURAN KRITIS:
1. Return HANYA SQL query
2. Mulai langsung dengan SELECT
3. TIDAK BOLEH ada teks lain, prefix, atau penjelasan
4. TIDAK BOLEH ada "AI:", "answer:", "jawaban:", atau apapun
5. TIDAK BOLEH ada markdown atau code blocks

EXAMPLES:
Intent: Cari semua penerbangan
Output: SELECT * FROM flight_prices;

Intent: Cari penerbangan Jakarta-Bali tanggal 7 Agustus
Output: SELECT fp.* FROM flight_prices fp INNER JOIN airports a1 ON fp.origin_code = a1.code INNER JOIN airports a2 ON fp.destination_code = a2.code WHERE a1.city = 'Jakarta' AND a2.city = 'Denpasar' AND fp.valid_from >= '2025-08-07' AND valid_to <= '2025-09-07';

Intent: Cari penerbangan Jakarta-Bali dengan harga termurah
Output: SELECT fp.* FROM flight_prices fp INNER JOIN airports a1 ON fp.origin_code = a1.code INNER JOIN airports a2 ON fp.destination_code = a2.code WHERE a1.city = 'Jakarta' AND a2.city = 'Denpasar' LIMIT 1;
"""

        understanding_prompt_ = ChatPromptTemplate.from_messages([
            ("system",understanding_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human","{question}")
        ])

        sql_prompt_ = ChatPromptTemplate.from_messages([
            ("system",sql_prompt),
            ("human", "Intent: {intent}\n\nGenerate SQL:")
        ])

        # === ✅ Buat instance history di luar agar bisa di-load dulu ===
        history = InMemoryChatMessageHistory(
            conn=conn, 
            conversation_id=self.conversation_id
        )
        print("Success Get History")
        
        # === ✅ Load messages ke cache sebelum invoke ===
        await history.aget_messages()
        print("Success Load Message History")

        def get_session_history(session_id: str):
            """Harus return instance yang sama"""
            return history

        chain = understanding_prompt_ | self.llm | StrOutputParser()
        understanding_chain = RunnableWithMessageHistory(
            chain,
            get_session_history=get_session_history,
            input_messages_key="question",
            history_messages_key="history",
        )
        
        intent_output = await understanding_chain.ainvoke(
            {
                "question": self.params.message,
                "context": context,
                "current_date": NOW.strftime("%Y-%m-%d")
            },
            config={"configurable": {"session_id": self.params.conversation_id}}
        )
        
        print(f"🧠 Intent: {intent_output}")
        
        # Extract intent
        if "QUERY_INTENT:" in intent_output:
            intent = intent_output.split("QUERY_INTENT:")[1].strip()
        else:
            intent = intent_output
        
        # Chain 2: Generate SQL tanpa memory (pure generation)
        print("Generating SQL...")
        sql_chain = sql_prompt_ | self.llm | StrOutputParser()
        
        raw_sql = await sql_chain.ainvoke({
            "intent": intent,
            "context": context
        })
        
        print(f"🔍 Raw SQL: {raw_sql}")
        
        # Clean and validate
        clean_sql = await self.clean_sql(raw_sql)
        
        if not self.validate_sql_output(clean_sql):
            raise ValueError(f"Invalid SQL generated: {raw_sql}")
        
        print(f"✅ Clean SQL: {clean_sql}")
        
        # Simpan SQL ke memory (optional, untuk tracking)
        # await history.aadd_message(AIMessage(content=f"[SQL Generated for: {question}]"))

        # # Generate SQL using LLM
        # formatted_prompt = prompt.format(context=context, question=self.params.message, current_date=NOW.strftime("%Y-%m-%d"))
        # sql_query = self.llm(formatted_prompt).strip()
        
        # # Clean up the response
        # if sql_query.startswith("```sql"):
        #     sql_query = sql_query[6:]
        # if sql_query.endswith("```"):
        #     sql_query = sql_query[:-3]

        try:
            # Execute SQL query
            results = await self.execute_query(conn=conn, sql_query=clean_sql)
            print("Success executing SQL")

            # Language Detection
            language = await self.language_detection()
            print("Success collect Language")

            # Report Agent
            report = await self.report_agent(question=self.params.message, result_query=results, language=language, conn=conn)
            print(f"REPORT: {report}")

            
            ## create message from bot
            # message_payload = CreateMessageRequest(
            #     conversation_id=conversation_id,
            #     content=report.content,
            #     message_type=MessageTypeEnum.answer,
            #     token_usage=report.response_metadata.get("token_usage", {}),
            #     created_by=created_by,
            #     metadata={}
            # ).transform()
            # await MessageRepository().create_message(conn=conn, payload=message_payload)

            # return MessageDataResponse(
            #     content=report.content,
            #     token_usage=report.response_metadata.get("token_usage", {}),
            #     created_at=datetime.now()
            # )

            # return MessageDataResponse(content=report.content,token_usage=report.response_metadata.get("token_usage", {}),created_at=datetime.now())
            return report
        
        except ProgrammingError as e:
            await conn.rollback() 
            print("---------ERROR---------")
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
                conversation_id=self.conversation_id,
                content=report.content,
                message_type=MessageTypeEnum.answer,
                token_usage={},
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
            conn: AsyncConnection,
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

        # === ✅ Buat instance history di luar agar bisa di-load dulu ===
        history = InMemoryChatMessageHistory(
            conn=conn, 
            conversation_id=self.params.conversation_id
        )
        print("Success Get History")
        
        # === ✅ Load messages ke cache sebelum invoke ===
        await history.aget_messages()
        print("Success Load Message History")

        def get_session_history(session_id: str):
            """Harus return instance yang sama"""
            return history

        prompt = ChatPromptTemplate.from_messages([
            ("system",prompt_template),
            MessagesPlaceholder(variable_name="history"),
            ("human","{question}")
        ])

        chain = prompt | self.llm | StrOutputParser()

        chain_with_history = RunnableWithMessageHistory(
            chain,
            get_session_history=get_session_history,
            input_messages_key="question",
            history_messages_key="history",
        )

        # 💾 Simpan pertanyaan user
        # await history.aadd_message(HumanMessage(content=self.params.message))

        response = await chain_with_history.ainvoke(
            {
                "question": question,
                "result_query": result_query,
                "language": language
            },
            config={"configurable": {"session_id": self.params.conversation_id}}
        )

        # 💾 Simpan response AI
        await history.aadd_message(AIMessage(content=response), conversation_id=self.conversation_id)

        return MessageDataResponse(
            content=response,
            token_usage={},
            created_at=datetime.now()
        )