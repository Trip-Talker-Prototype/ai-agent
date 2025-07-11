from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import RowMapping, select, func, cast, insert, desc

from api.flights.interface import FlightsInterface
from api.flights.schemas import FlightsFilter
from api.flights.models import flight_price

class FlightRepositories(FlightsInterface):
    async def get_flights(
            self, 
            conn: AsyncConnection, 
            filter: FlightsFilter
        ) -> Sequence[RowMapping]:
        stmt = select(
            flight_price.c.id,
            flight_price.c.flight_number,
            flight_price.c.base_price,
            flight_price.c.tax,
            flight_price.c.fee
        )

        stmt = stmt.limit(filter.limit).offset(filter.offset)

        try:
            # Execute paginated query
            result = await conn.execute(statement=stmt)
            return result.mappings().fetchall()
        except Exception as e:
            raise e