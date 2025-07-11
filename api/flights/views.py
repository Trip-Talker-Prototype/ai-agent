from typing import Annotated, Text
from fastapi import APIRouter, Path, Query, Request, status

from api.database.database import DBConnection
from api.flights.services import FlightServices
from api.flights.repositories import FlightRepositories
from api.flights.schemas import FlightsFilter, FlightsVectorRequest

flights_router = APIRouter(prefix="/api/v1/flights", tags=["Flights"])

@flights_router.get("/")
async def get_flights(
    request: Request,
    db: DBConnection,
    query_parameter: Annotated[FlightsFilter, Query()],
):
    flights_service = FlightServices(flights_repo=FlightRepositories())
    flights = await flights_service.get_flights(
        conn=db,
        filter=query_parameter
    )

    results = [flight for flight in flights]

    return results

@flights_router.post("/vector_store")
async def vector_stores(
    request: Request,
    schemas: FlightsVectorRequest
):
    flights_service = FlightServices(flights_repo=FlightRepositories())
    vectors = await flights_service.vector_embeddings(
        schemas=schemas
    )
    return {
        "message": "Vector embeddings successfully stored",
        "collection_name": vectors.collection_name
    }