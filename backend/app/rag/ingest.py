from pathlib import Path

from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeChunk
from app.rag.corpus import CorpusError, chunk_text, load_sources_ledger, parse_source_file
from app.rag.embeddings import EmbeddingProvider


def ingest_corpus(
    db: Session, content_dir: Path, sources_md_path: Path, embedder: EmbeddingProvider
) -> int:
    """Ingest corpus/content/*.md into knowledge_chunks, refusing anything unlicensed.

    Idempotent: re-running replaces a source's existing chunks rather than duplicating them.
    Returns the number of chunks written.
    """
    ledger = load_sources_ledger(sources_md_path)
    total_chunks = 0

    for path in sorted(content_dir.glob("*.md")):
        doc = parse_source_file(path)
        entry = ledger.get(doc.id)
        if entry is None:
            raise CorpusError(
                f"{path.name}: source id {doc.id!r} is not listed in {sources_md_path.name} "
                "with a license -- refusing to ingest"
            )

        db.query(KnowledgeChunk).filter(KnowledgeChunk.source_id == doc.id).delete(
            synchronize_session=False
        )

        chunks = chunk_text(doc.body)
        embeddings = embedder.embed(chunks)
        for index, (chunk_content, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
            db.add(
                KnowledgeChunk(
                    source_id=doc.id,
                    title=doc.title,
                    author=doc.author,
                    license=entry.license,
                    evidence_strength=doc.evidence_strength,
                    chunk_index=index,
                    content=chunk_content,
                    chunk_metadata={"source_type": entry.source_type},
                    embedding=embedding,
                )
            )
            total_chunks += 1

    db.commit()
    return total_chunks
