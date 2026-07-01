"""Ingest corpus/content/*.md into the knowledge_chunks table.

    python -m scripts.ingest_corpus

Refuses to ingest any file whose id isn't listed with a license in corpus/sources.md
(SAD Phase 3.1 -- license-first ingestion).
"""

from pathlib import Path

from app.db.session import SessionLocal
from app.rag.embeddings import get_embedding_provider
from app.rag.ingest import ingest_corpus

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = REPO_ROOT / "corpus" / "content"
SOURCES_MD = REPO_ROOT / "corpus" / "sources.md"


def main() -> None:
    db = SessionLocal()
    try:
        count = ingest_corpus(db, CONTENT_DIR, SOURCES_MD, get_embedding_provider())
        print(f"Ingested {count} chunk(s) from {CONTENT_DIR}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
