from fastapi import FastAPI

from dotenv import load_dotenv

from api.chatbot.views import chat_router
from api.flights.views import flights_router
from api.conversations.views import conversation_router

load_dotenv()

app = FastAPI()
app.include_router(chat_router)
app.include_router(flights_router)
app.include_router(conversation_router)

@app.get("/health")
def health_check():
    return "Health Chek is success"