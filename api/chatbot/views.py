from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import StreamingResponse

from api.chatbot.services import ChatBotAI
from api.chatbot.schemas import APIMessageParams, ChatModelResponse, ChatModelErrorResponse
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
    response:Response,
    db: DBConnection,
    params: APIMessageParams
):
    try:
        chat = await ChatBotAI(params=params).chat_v2(conn=db, params=params)
        return ChatModelResponse(resp=chat)
    except HTTPException as ex:
        response.status_code = ex.status_code
        return ChatModelErrorResponse(
            message=ex.detail
        )
    except Exception as ex:
        response.status_code = 500
        return ChatModelErrorResponse(
            message="Failed asking the model"
        )