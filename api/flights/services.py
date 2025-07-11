from langchain_community.llms import OpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document

from sqlalchemy.ext.asyncio import AsyncConnection

from api.flights.repositories import FlightRepositories
from api.flights.schemas import FlightsFilter, FlightsVectorRequest
from api.database.client import connection_url

class FlightServices:
    def __init__(
            self,
            flights_repo: FlightRepositories
        ):
        self.__flights_repo = flights_repo
        
        self.embeddings = OpenAIEmbeddings()
        self.llm = OpenAI(temperature = 0)
        self.memory = ConversationBufferMemory(return_messages=True)

    async def get_flights(
            self,
            conn: AsyncConnection,
            filter: FlightsFilter
        ):
        result = await self.__flights_repo.get_flights(
            conn=conn,
            filter=filter
        )
        return result
    
    async def vector_embeddings(
            self,
            schemas: FlightsVectorRequest,
    ):
        try:
            docs = Document(
                page_content=schemas.schemas,
            )

            self.vector_store = PGVector.from_documents(
                documents=[docs],
                embedding=self.embeddings,
                connection_string=connection_url,
                collection_name="ai_agent_gogo"
            )
            
            print("Vector store berhasil disetup!")
            return self.vector_store
            
        except Exception as e:
            print(f"Error setting up vector store: {e}")

        
