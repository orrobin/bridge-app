"""add pgvector extension and knowledge_chunks table

Revision ID: 62d2bc071ea6
Revises: 69c03e05fd67
Create Date: 2026-07-01 15:00:00.000000

NOTE: Requires the `vector` extension to be installed on the Postgres server
(see corpus/README or TASKS.md T1.3). Not yet applied/verified in this
environment because pgvector could not be compiled here (no MSVC build
tools available with elevation). Apply with `alembic upgrade head` once
the extension is available.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector.sqlalchemy

# revision identifiers, used by Alembic.
revision: str = '62d2bc071ea6'
down_revision: Union[str, Sequence[str], None] = '69c03e05fd67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.create_table(
        'knowledge_chunks',
        sa.Column('source_id', sa.String(length=128), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=False),
        sa.Column('license', sa.String(length=64), nullable=False),
        sa.Column('evidence_strength', sa.String(length=64), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(1536), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_knowledge_chunks_source_id'), 'knowledge_chunks', ['source_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_knowledge_chunks_source_id'), table_name='knowledge_chunks')
    op.drop_table('knowledge_chunks')
    op.execute('DROP EXTENSION IF EXISTS vector')
