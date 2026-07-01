import re
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeChunk

_WORD_RE = re.compile(r"[a-zA-Z0-9]+")


def vector_search(db: Session, query_embedding: list[float], top_k: int) -> list[KnowledgeChunk]:
    return (
        db.query(KnowledgeChunk)
        .order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
        .all()
    )


def lexical_search(db: Session, query_text: str, top_k: int) -> list[KnowledgeChunk]:
    """Postgres full-text search, OR-ing query terms (SAD Phase 3.3).

    Uses OR rather than plainto_tsquery's implicit AND: a natural-language
    question rarely shares every content word with a relevant chunk, and an
    AND match would drop it from the candidate set entirely instead of just
    ranking it lower.
    """
    words = _WORD_RE.findall(query_text)
    if not words:
        return []

    tsquery = func.to_tsquery("english", " | ".join(words))
    tsvector = func.to_tsvector("english", KnowledgeChunk.content)
    return (
        db.query(KnowledgeChunk)
        .filter(tsvector.op("@@")(tsquery))
        .order_by(func.ts_rank_cd(tsvector, tsquery).desc())
        .limit(top_k)
        .all()
    )


def reciprocal_rank_fusion(
    rankings: list[list[uuid.UUID]], k: int = 60
) -> list[tuple[uuid.UUID, float]]:
    """Combine multiple ranked id lists via Reciprocal Rank Fusion.

    score(doc) = sum over rankings of 1 / (k + rank), 1-indexed rank, 0 for lists
    the doc doesn't appear in. Returns (id, score) sorted by score descending.
    """
    scores: dict[uuid.UUID, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def hybrid_search(
    db: Session, query_text: str, query_embedding: list[float], top_k: int
) -> list[KnowledgeChunk]:
    """Vector + lexical search fused with RRF (SAD Phase 3.3)."""
    # Wider candidate pools than top_k so fusion has enough to work with.
    candidate_k = max(top_k * 4, 20)
    vector_hits = vector_search(db, query_embedding, candidate_k)
    lexical_hits = lexical_search(db, query_text, candidate_k)

    by_id = {chunk.id: chunk for chunk in [*vector_hits, *lexical_hits]}
    fused = reciprocal_rank_fusion(
        [[chunk.id for chunk in vector_hits], [chunk.id for chunk in lexical_hits]]
    )
    return [by_id[doc_id] for doc_id, _ in fused[:top_k]]
