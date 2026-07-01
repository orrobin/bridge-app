import re
from dataclasses import dataclass
from pathlib import Path

_FRONT_MATTER_RE = re.compile(r"^(.*?)\n---\n(.*)$", re.DOTALL)
_LEDGER_ROW_RE = re.compile(
    r"^\|\s*([\w-]+)\s*\|.*?\|.*?\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|.*\|$"
)


class CorpusError(ValueError):
    """Raised when a source file is missing required front matter or a license."""


@dataclass(frozen=True)
class SourceDocument:
    id: str
    title: str
    author: str
    evidence_strength: str
    body: str


@dataclass(frozen=True)
class LedgerEntry:
    source_type: str
    license: str


def parse_source_file(path: Path) -> SourceDocument:
    raw = path.read_text(encoding="utf-8")
    match = _FRONT_MATTER_RE.match(raw)
    if not match:
        raise CorpusError(f"{path.name}: missing '---' front-matter separator")

    header, body = match.group(1), match.group(2).strip()
    fields: dict[str, str] = {}
    for line in header.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise CorpusError(f"{path.name}: malformed front-matter line {line!r}")
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()

    required = {"id", "title", "author", "evidence_strength"}
    missing = required - fields.keys()
    if missing:
        raise CorpusError(f"{path.name}: missing front-matter field(s) {sorted(missing)}")

    return SourceDocument(
        id=fields["id"],
        title=fields["title"],
        author=fields["author"],
        evidence_strength=fields["evidence_strength"],
        body=body,
    )


def load_sources_ledger(sources_md_path: Path) -> dict[str, LedgerEntry]:
    """Parse the markdown table in corpus/sources.md into {id: LedgerEntry}."""
    ledger: dict[str, LedgerEntry] = {}
    for line in sources_md_path.read_text(encoding="utf-8").splitlines():
        match = _LEDGER_ROW_RE.match(line.strip())
        if not match:
            continue
        source_id, source_type, license_ = match.groups()
        if source_id in {"id", "---"} or set(source_id) == {"-"}:
            continue
        ledger[source_id] = LedgerEntry(source_type=source_type, license=license_)
    return ledger


def chunk_text(text: str, max_chars: int = 800) -> list[str]:
    """Group paragraphs (blank-line separated) into chunks up to ~max_chars."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks
