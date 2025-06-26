from fastapi import FastAPI

from dotenv import load_dotenv

from api.chatbot.views import chat_router

load_dotenv()

app = FastAPI()
app.include_router(chat_router)