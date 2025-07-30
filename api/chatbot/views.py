from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from api.chatbot.service import ChatBotAI
from api.chatbot.schemas import APIMessageParams
from api.database.database import DBConnection

chat_router = APIRouter(prefix='/api/v1/chat', tags=["Chat"])

@chat_router.post("/")
async def chat(
    request: Request,
    params: APIMessageParams
):
    chat = await ChatBotAI(params=params).chat()
    return chat

@chat_router.post("/v2")
async def chat_v2(
    request: Request,
    db: DBConnection,
    params: APIMessageParams
):
    chat = await ChatBotAI(params=params).chat_v2(conn=db, params=params)
    return chat
    