from pathlib import Path

import pytest
from sqlalchemy import text

from app.db.session import SessionLocal
from app.models.knowledge import EMBEDDING_DIM
from app.rag.embeddings import HashingBagOfWordsEmbedder
from app.rag.ingest import ingest_corpus
from app.rag.retrieval import hybrid_search, vector_search

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = REPO_ROOT / "corpus" / "content"
SOURCES_MD = REPO_ROOT / "corpus" / "sources.md"

# Hand-labeled golden set: natural-language question -> expected source_id.
# Picked to include queries that don't share the target doc's exact vocabulary,
# which is where fusing in lexical search should help a crude vector embedder.
GOLDEN_SET = [
    (
        "how can I tell if the person I am texting is losing interest",
        "reading-disinterest-signals",
    ),
    (
        "my match has been giving short replies should I worry theyre not interested anymore",
        "reading-disinterest-signals",
    ),
    (
        "how do I bring up wanting to slow down before we meet in person",
        "boundaries-and-consent-early-dating",
    ),
    (
        "I think my joke came across wrong and now things feel awkward between us",
        "repair-after-miscommunication",
    ),
    (
        "we had an awkward exchange yesterday and I want to smooth things over",
        "repair-after-miscommunication",
    ),
]


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


def _rank_of_expected(chunks, expected_source_id: str) -> float:
    for rank, chunk in enumerate(chunks, start=1):
        if chunk.source_id == expected_source_id:
            return rank
    return float("inf")


def test_hybrid_search_has_better_mean_reciprocal_rank_than_vector_only():
    embedder = HashingBagOfWordsEmbedder(dimension=EMBEDDING_DIM)
    db = SessionLocal()
    try:
        ingest_corpus(db, CONTENT_DIR, SOURCES_MD, embedder)

        vector_reciprocal_ranks = []
        hybrid_reciprocal_ranks = []
        for question, expected_source_id in GOLDEN_SET:
            (query_embedding,) = embedder.embed([question])

            vector_only = vector_search(db, query_embedding, top_k=16)
            hybrid = hybrid_search(db, question, query_embedding, top_k=16)

            vector_reciprocal_ranks.append(1.0 / _rank_of_expected(vector_only, expected_source_id))
            hybrid_reciprocal_ranks.append(1.0 / _rank_of_expected(hybrid, expected_source_id))

        vector_mrr = sum(vector_reciprocal_ranks) / len(vector_reciprocal_ranks)
        hybrid_mrr = sum(hybrid_reciprocal_ranks) / len(hybrid_reciprocal_ranks)

        assert hybrid_mrr > vector_mrr
        assert all(h >= v for h, v in zip(hybrid_reciprocal_ranks, vector_reciprocal_ranks))
    finally:
        db.close()
