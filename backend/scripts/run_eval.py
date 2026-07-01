"""Offline eval report: retrieval recall@k + citation-accuracy spot check.

    python -m scripts.run_eval

Requires the corpus to already be ingested (python -m scripts.ingest_corpus)
against a pgvector-enabled Postgres. Prints a report; does not assert/fail --
intended to run as a non-blocking CI step (see .github/workflows/ci.yml).
"""

from pathlib import Path

from app.db.session import SessionLocal
from app.rag.embeddings import get_embedding_provider
from app.rag.eval import evaluate_citation_accuracy, evaluate_retrieval
from app.rag.ingest import ingest_corpus

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = REPO_ROOT / "corpus" / "content"
SOURCES_MD = REPO_ROOT / "corpus" / "sources.md"


def main() -> None:
    db = SessionLocal()
    try:
        embedder = get_embedding_provider()
        ingest_corpus(db, CONTENT_DIR, SOURCES_MD, embedder)

        retrieval_report = evaluate_retrieval(db, embedder)
        print(f"Retrieval eval ({retrieval_report.num_queries} golden-set queries):")
        for k, recall in sorted(retrieval_report.recall_at_k.items()):
            print(f"  Recall@{k}: {recall:.0%}")

        citation_report = evaluate_citation_accuracy(db, embedder, SOURCES_MD)
        print(
            f"Citation accuracy: {citation_report.accuracy:.0%} "
            f"({citation_report.valid_citations}/{citation_report.total_citations} "
            "citations reference a licensed corpus source)"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
