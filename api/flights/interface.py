from typing import Protocol, Sequence
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import RowMapping

from api.flights.schemas import FlightsFilter


class FlightsInterface(Protocol):
    async def get_flights(
        self, 
        conn: AsyncConnection,
        filter: FlightsFilter
    ) -> Sequence[RowMapping]: ...

    async def vector_stores(
        self,
        conn: AsyncConnection,
    ): ...