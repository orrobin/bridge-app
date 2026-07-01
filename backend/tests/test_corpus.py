from pathlib import Path

import pytest

from app.rag.corpus import CorpusError, chunk_text, load_sources_ledger, parse_source_file

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = REPO_ROOT / "corpus" / "content"
SOURCES_MD = REPO_ROOT / "corpus" / "sources.md"


def test_all_seed_content_files_are_listed_in_the_ledger():
    ledger = load_sources_ledger(SOURCES_MD)
    content_files = sorted(CONTENT_DIR.glob("*.md"))
    assert len(content_files) >= 5

    for path in content_files:
        doc = parse_source_file(path)
        assert doc.id in ledger, f"{path.name} (id={doc.id}) missing from sources.md ledger"
        assert ledger[doc.id].license


def test_parse_source_file_requires_front_matter(tmp_path):
    bad_file = tmp_path / "bad.md"
    bad_file.write_text("no front matter here", encoding="utf-8")
    with pytest.raises(CorpusError):
        parse_source_file(bad_file)


def test_parse_source_file_requires_all_fields(tmp_path):
    bad_file = tmp_path / "bad.md"
    bad_file.write_text("id: x\ntitle: Y\n---\nbody text", encoding="utf-8")
    with pytest.raises(CorpusError):
        parse_source_file(bad_file)


def test_chunk_text_splits_long_text_on_paragraph_boundaries():
    paragraphs = [f"Paragraph {i} " + "word " * 40 for i in range(5)]
    text = "\n\n".join(paragraphs)
    chunks = chunk_text(text, max_chars=200)
    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)


def test_chunk_text_keeps_short_text_as_one_chunk():
    chunks = chunk_text("Just one short paragraph.", max_chars=800)
    assert chunks == ["Just one short paragraph."]
