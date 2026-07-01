import uuid

import pytest
from sqlalchemy import text

from app.db.session import SessionLocal
from app.models.knowledge import EMBEDDING_DIM, KnowledgeChunk


def _pgvector_available() -> bool:
    db = SessionLocal()
    try:
        row = db.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).first()
        return row is not None
    finally:
        db.close()


pytestmark = pytest.mark.skipif(
    not _pgvector_available(),
    reason="pgvector extension not installed in this environment (see TASKS.md T1.3)",
)


def _make_chunk(embedding: list[float], suffix: str) -> KnowledgeChunk:
    return KnowledgeChunk(
        source_id=f"test-source-{suffix}",
        title=f"Test chunk {suffix}",
        author="Test Author",
        license="test-fixture",
        evidence_strength="n/a",
        chunk_index=0,
        content=f"Fixture content {suffix}",
        chunk_metadata={},
        embedding=embedding,
    )


def test_cosine_similarity_returns_nearest_row():
    close_vector = [1.0] + [0.0] * (EMBEDDING_DIM - 1)
    far_vector = [0.0, 1.0] + [0.0] * (EMBEDDING_DIM - 2)
    query_vector = [0.9] + [0.0] * (EMBEDDING_DIM - 1)

    suffix = uuid.uuid4().hex
    close_chunk = _make_chunk(close_vector, f"close-{suffix}")
    far_chunk = _make_chunk(far_vector, f"far-{suffix}")

    db = SessionLocal()
    try:
        db.add_all([close_chunk, far_chunk])
        db.commit()

        nearest = (
            db.query(KnowledgeChunk)
            .filter(KnowledgeChunk.source_id.in_([close_chunk.source_id, far_chunk.source_id]))
            .order_by(KnowledgeChunk.embedding.cosine_distance(query_vector))
            .first()
        )
        assert nearest is not None
        assert nearest.id == close_chunk.id
    finally:
        db.query(KnowledgeChunk).filter(
            KnowledgeChunk.source_id.in_([close_chunk.source_id, far_chunk.source_id])
        ).delete(synchronize_session=False)
        db.commit()
        db.close()
