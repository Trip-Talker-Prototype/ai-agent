from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import StreamingResponse

from api.conversations.services import ChatBotAI
from api.conversations.schemas import APIMessageParams, ChatModelResponse, ChatModelErrorResponse
from api.database.database import DBConnection

conversation_router = APIRouter(prefix='/api/v1/conversations', tags=["Conversations"])

@conversation_router.post("/")
async def chat_v2(
    request: Request,
    response:Response,
    db: DBConnection,
    params: APIMessageParams
):
    try:
        chat = await ChatBotAI(params=params).create_conversation(conn=db)
        import pdb;pdb.set_trace()
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