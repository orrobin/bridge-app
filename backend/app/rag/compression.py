import re

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_TOKEN_RE = re.compile(r"[a-z0-9']+")


def _token_count(text: str) -> int:
    """Whitespace-token proxy for LLM token count -- good enough to compare relative sizes."""
    return len(text.split())


def _overlap_score(sentence: str, query_terms: set[str]) -> int:
    sentence_terms = set(_TOKEN_RE.findall(sentence.lower()))
    return len(sentence_terms & query_terms)


def compress_chunk(chunk_text: str, query: str, max_sentences: int = 2) -> str:
    """Keep only the most query-relevant sentences from a chunk, in original order."""
    sentences = [s.strip() for s in _SENTENCE_RE.split(chunk_text) if s.strip()]
    if len(sentences) <= max_sentences:
        return chunk_text

    query_terms = set(_TOKEN_RE.findall(query.lower()))
    ranked = sorted(
        range(len(sentences)), key=lambda i: _overlap_score(sentences[i], query_terms), reverse=True
    )
    keep_indices = sorted(ranked[:max_sentences])
    return " ".join(sentences[i] for i in keep_indices)


def compress_context(chunks: list[str], query: str, max_sentences_per_chunk: int = 2) -> str:
    """Compress a list of retrieved chunks into a single, token-budgeted context block."""
    compressed = [compress_chunk(chunk, query, max_sentences_per_chunk) for chunk in chunks]
    return "\n\n".join(compressed)
