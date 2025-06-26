from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from api.chatbot.service import ChatBotAI

chat_router = APIRouter(prefix='/api/v1/chat', tags=["Chat"])

@chat_router.post("/")
async def chat(
    request: Request,
    prompt: str
):
    chat = await ChatBotAI(prompt=prompt).chat()
    return chat

    