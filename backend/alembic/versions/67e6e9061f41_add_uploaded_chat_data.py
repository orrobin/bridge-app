"""add uploaded_chat_data (redacted, short-TTL target-party data)

Revision ID: 67e6e9061f41
Revises: 69c03e05fd67
Create Date: 2026-07-01 16:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '67e6e9061f41'
down_revision: Union[str, Sequence[str], None] = '69c03e05fd67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'uploaded_chat_data',
        sa.Column('thread_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('redacted_turns', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False
        ),
        sa.ForeignKeyConstraint(['thread_id'], ['conversation_threads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_uploaded_chat_data_expires_at'), 'uploaded_chat_data', ['expires_at'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_uploaded_chat_data_expires_at'), table_name='uploaded_chat_data')
    op.drop_table('uploaded_chat_data')
