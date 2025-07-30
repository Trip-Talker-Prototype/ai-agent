from typing import Annotated, Any, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from api.database.client import engine


async def get_connection() -> AsyncGenerator[Any, Any]:
    async with engine.connect() as connection:
        yield connection


DBConnection = Annotated[AsyncConnection, Depends(get_connection)]
