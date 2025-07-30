import uuid

from pgvector.sqlalchemy import Vector

from sqlalchemy import Table, Column, String, Numeric, Date, UUID, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from api.database.client import metadata

langchain_pg_embedding = Table(
    'langchain_pg_embedding',
    metadata,
    Column("collection_id", UUID()),
    Column("embedding", Vector, nullable=True),
    Column("document", Text, nullable=True),
    Column("cmetadata", JSONB, nullable=True),
    Column("custom_id", Text, nullable=True),
    Column("uuid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
)