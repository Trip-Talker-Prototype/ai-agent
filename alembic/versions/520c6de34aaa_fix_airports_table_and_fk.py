"""fix_airports_table_and_fk

Revision ID: 520c6de34aaa
Revises: 080e2cf80557
Create Date: 2025-08-28 22:46:23.417120

"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '520c6de34aaa'
down_revision: Union[str, Sequence[str], None] = '080e2cf80557'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('airports',
        sa.Column('code', sa.String(length=3), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('city', sa.String(length=50), nullable=False),
        sa.Column('country', sa.String(length=50), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('code')
    )

    current_time = datetime.now()
    
    # Step 2: Insert data bandara-bandara umum
    airports_table = sa.table('airports',
        sa.column('code', sa.String),
        sa.column('name', sa.String),
        sa.column('city', sa.String),
        sa.column('country', sa.String),
        sa.column('timezone', sa.String),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime)
    )
    
    # Data bandara umum di Asia Tenggara
    common_airports = [
        {
            'code': 'CGK', 'name': 'Soekarno-Hatta International Airport',
            'city': 'Jakarta', 'country': 'Indonesia', 'timezone': 'Asia/Jakarta',
            'created_at': current_time, 'updated_at': current_time
        },
        {
            'code': 'DPS', 'name': 'Ngurah Rai International Airport',
            'city': 'Denpasar', 'country': 'Indonesia', 'timezone': 'Asia/Makassar',
            'created_at': current_time, 'updated_at': current_time
        },
        {
            'code': 'SUB', 'name': 'Juanda International Airport',
            'city': 'Surabaya', 'country': 'Indonesia', 'timezone': 'Asia/Jakarta',
            'created_at': current_time, 'updated_at': current_time
        },
        {
            'code': 'SIN', 'name': 'Changi Airport',
            'city': 'Singapore', 'country': 'Singapore', 'timezone': 'Asia/Singapore',
            'created_at': current_time, 'updated_at': current_time
        },
        {
            'code': 'KUL', 'name': 'Kuala Lumpur International Airport',
            'city': 'Kuala Lumpur', 'country': 'Malaysia', 'timezone': 'Asia/Kuala_Lumpur',
            'created_at': current_time, 'updated_at': current_time
        },
        {
            'code': 'BKK', 'name': 'Suvarnabhumi Airport',
            'city': 'Bangkok', 'country': 'Thailand', 'timezone': 'Asia/Bangkok',
            'created_at': current_time, 'updated_at': current_time
        }
    ]
    
    op.bulk_insert(airports_table, common_airports)
    
    op.create_foreign_key(
        'fk_flight_prices_origin_code',
        'flight_prices', 'airports',
        ['origin'], ['code']
    )
    op.create_foreign_key(
        'fk_flight_prices_destination_code',
        'flight_prices', 'airports',
        ['destination'], ['code']
    )
    
    op.alter_column('flight_prices', 'origin', nullable=False)
    op.alter_column('flight_prices', 'destination', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('airports')
