from sqlalchemy import Table, Column, String, Numeric, Date, UUID, ForeignKey
from sqlalchemy.sql import func

from api.models.base import get_audit_columns
from api.database.client import metadata

import uuid

flight_price = Table(
    "flight_prices",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("flight_number", String(20), nullable=False),
    Column("class", String(20), nullable=False),
    Column("base_price", Numeric(10, 2), nullable=False),
    Column("tax", Numeric(10, 2), nullable=False),
    Column("fee", Numeric(10, 2), nullable=False),
    Column("currency", String(3), default='USD'),
    Column("valid_from", Date, nullable=False),
    Column("valid_to", Date, nullable=False),
    
    # Kolom baru dengan foreign key
    Column("origin", String(3), ForeignKey('airports.code'), nullable=False),
    Column("destination", String(3), ForeignKey('airports.code'), nullable=False),
    
    *get_audit_columns()
)

airports = Table(
    "airports",
    metadata,
    Column("code", String(3), primary_key=True),  # Kode IATA (CGK, DPS, etc)
    Column("name", String(100), nullable=False),  # Nama bandara
    Column("city", String(50), nullable=False),   # Kota
    Column("country", String(50), nullable=False), # Negara
    Column("timezone", String(50)),               # Timezone
    *get_audit_columns()
)