from pydantic import BaseModel

class FlightsFilter(BaseModel):
    limit: int = 10
    offset: int = 0
    search: str | None = None


class FlightsVectorRequest(BaseModel):
    schemas: str