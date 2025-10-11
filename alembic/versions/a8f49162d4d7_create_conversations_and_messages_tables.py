"""create conversations and messages tables

Revision ID: a8f49162d4d7
Revises: 520c6de34aaa
Create Date: 2025-10-10 05:14:47.247881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from api.models.base import get_audit_columns
from api.conversations.models import MessageTypeEnum


# revision identifiers, used by Alembic.
revision: str = 'a8f49162d4d7'
down_revision: Union[str, Sequence[str], None] = '520c6de34aaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('conversations',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        *get_audit_columns(),
    )
    
    op.create_table('messages',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.Enum(MessageTypeEnum, name='message_type_enum'), nullable=False),
        sa.Column('token_usage', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            name="fk_message_conversation", columns=["conversation_id"], refcolumns=["conversations.id"]
        ),
        *get_audit_columns(),
    )
        
def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("conversation")
    op.drop_table("messages")

