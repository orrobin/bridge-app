from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

# text-embedding-3-small dimension; revisit if the embedding model choice changes (SAD Phase 8.2).
EMBEDDING_DIM = 1536


class KnowledgeChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A retrievable, license-tagged chunk of the corpus (SAD Phase 3.1/3.2).

    Ingestion (Epic 4) must refuse to write a row here without a license tag,
    since `corpus/sources.md` is the ledger of what's allowed to be indexed.
    """

    __tablename__ = "knowledge_chunks"

    source_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    license: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_strength: Mapped[str] = mapped_column(String(64), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
