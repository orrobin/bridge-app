from pathlib import Path

import pytest
from sqlalchemy import text

from app.db.session import SessionLocal
from app.models.knowledge import EMBEDDING_DIM, KnowledgeChunk
from app.rag.embeddings import HashingBagOfWordsEmbedder
from app.rag.ingest import ingest_corpus

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = REPO_ROOT / "corpus" / "content"
SOURCES_MD = REPO_ROOT / "corpus" / "sources.md"


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


def test_ingest_corpus_then_smoke_query_finds_relevant_chunk():
    embedder = HashingBagOfWordsEmbedder(dimension=EMBEDDING_DIM)
    db = SessionLocal()
    try:
        count = ingest_corpus(db, CONTENT_DIR, SOURCES_MD, embedder)
        assert count >= 8

        (query_vector,) = embedder.embed(
            ["how do I tell if someone is losing interest without over-reading it"]
        )
        top_matches = (
            db.query(KnowledgeChunk)
            .order_by(KnowledgeChunk.embedding.cosine_distance(query_vector))
            .limit(3)
            .all()
        )
        top_source_ids = {chunk.source_id for chunk in top_matches}
        assert "reading-disinterest-signals" in top_source_ids
    finally:
        db.close()
