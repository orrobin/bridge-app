from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.agents.analyst import HeuristicAnalystProvider
from app.agents.strategy import HeuristicStrategyProvider
from app.rag.corpus import load_sources_ledger
from app.rag.embeddings import EmbeddingProvider
from app.rag.golden_set import GOLDEN_SET
from app.rag.retrieval import hybrid_search

# Sample redacted conversations for the citation-accuracy spot check (Epic 4-7
# already cover behavior in depth; this is just a report over realistic inputs).
_SAMPLE_CONVERSATIONS = [
    "SPEAKER_1: hey, how's your week been?\nSPEAKER_2: pretty good, yours?",
    "SPEAKER_1: I think I might be overthinking your last reply\n"
    "SPEAKER_2: no you're fine, just busy",
    "SPEAKER_1: would you want to grab coffee this weekend?\nSPEAKER_2: I'd love that!",
]


@dataclass(frozen=True)
class RetrievalEvalReport:
    recall_at_k: dict[int, float]
    num_queries: int


@dataclass(frozen=True)
class CitationEvalReport:
    total_citations: int
    valid_citations: int

    @property
    def accuracy(self) -> float:
        if self.total_citations == 0:
            return 0.0
        return self.valid_citations / self.total_citations


def evaluate_retrieval(
    db: Session, embedder: EmbeddingProvider, ks: tuple[int, ...] = (1, 3, 5)
) -> RetrievalEvalReport:
    """Recall@k: does the expected source_id appear anywhere in the top-k hybrid results."""
    hits: dict[int, int] = {k: 0 for k in ks}
    max_k = max(ks)

    for question, expected_source_id in GOLDEN_SET:
        (query_embedding,) = embedder.embed([question])
        results = hybrid_search(db, question, query_embedding, top_k=max_k)
        result_source_ids = [chunk.source_id for chunk in results]
        for k in ks:
            if expected_source_id in result_source_ids[:k]:
                hits[k] += 1

    recall_at_k = {k: hits[k] / len(GOLDEN_SET) for k in ks}
    return RetrievalEvalReport(recall_at_k=recall_at_k, num_queries=len(GOLDEN_SET))


def evaluate_citation_accuracy(
    db: Session, embedder: EmbeddingProvider, sources_md_path: Path
) -> CitationEvalReport:
    """Spot check: every citation emitted by the heuristic Analyst/Strategy providers
    must reference a source_id actually listed (with a license) in the corpus ledger.
    """
    ledger = load_sources_ledger(sources_md_path)
    analyst = HeuristicAnalystProvider()
    strategy = HeuristicStrategyProvider()

    total = 0
    valid = 0
    for conversation in _SAMPLE_CONVERSATIONS:
        (query_embedding,) = embedder.embed([conversation])
        retrieved = hybrid_search(db, conversation, query_embedding, top_k=3)
        retrieved_context = [(chunk.source_id, chunk.content) for chunk in retrieved]

        for hypothesis in analyst.analyze(conversation, retrieved_context):
            for citation in hypothesis.citations:
                total += 1
                valid += citation in ledger

        strategy_output = strategy.generate(conversation, retrieved_context)
        for option in strategy_output.options:
            for citation in option.citations:
                total += 1
                valid += citation in ledger

    return CitationEvalReport(total_citations=total, valid_citations=valid)
