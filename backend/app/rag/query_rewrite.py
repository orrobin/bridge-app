import re

_TOKEN_RE = re.compile(r"[a-z0-9']+")
_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "i", "you", "he",
    "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "its",
    "our", "their", "this", "that", "these", "those", "and", "or", "but", "if", "so", "of",
    "to", "in", "on", "at", "for", "with", "about", "as", "do", "does", "did", "not", "what",
    "how", "why", "when", "where", "who", "just", "really", "think", "know", "like", "get",
}


def _salient_terms(text: str) -> list[str]:
    seen: list[str] = []
    for token in _TOKEN_RE.findall(text.lower()):
        if len(token) < 4 or token in _STOPWORDS:
            continue
        if token not in seen:
            seen.append(token)
    return seen


def rewrite_query(raw_question: str, conversation_context: list[str], max_terms: int = 6) -> str:
    """Expand a vague question with salient terms drawn from recent conversation context.

    Deterministic, heuristic expansion (no LLM call) -- good enough to turn "is she into
    me?" into something retrieval can actually match against, without adding network
    dependency/cost/flakiness to every retrieval call. SAD Phase 3.3 notes an LLM-based
    HyDE/decomposition rewrite as the fuller version; this is the MVP-scoped slice.
    """
    question_terms = set(_salient_terms(raw_question))
    added: list[str] = []
    for turn in reversed(conversation_context):
        for term in _salient_terms(turn):
            if term not in question_terms and term not in added:
                added.append(term)
            if len(added) >= max_terms:
                break
        if len(added) >= max_terms:
            break

    if not added:
        return raw_question
    return f"{raw_question} {' '.join(added)}"
