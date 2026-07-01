"""add full-text-search GIN index on knowledge_chunks.content

Revision ID: eaab4895086d
Revises: 62d2bc071ea6
Create Date: 2026-07-01 17:00:00.000000

NOTE: depends on knowledge_chunks (pgvector-blocked locally, see 62d2bc071ea6). Verified
in CI the same way -- see TASKS.md T1.3/T5.1.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'eaab4895086d'
down_revision: Union[str, Sequence[str], None] = '62d2bc071ea6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_content_fts ON knowledge_chunks "
        "USING GIN (to_tsvector('english', content))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX ix_knowledge_chunks_content_fts")
