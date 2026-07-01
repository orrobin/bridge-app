import math

from app.rag.embeddings import HashingBagOfWordsEmbedder


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def test_embedding_is_deterministic():
    embedder = HashingBagOfWordsEmbedder(dimension=64)
    a = embedder.embed(["bids for connection in relationships"])[0]
    b = embedder.embed(["bids for connection in relationships"])[0]
    assert a == b


def test_similar_texts_are_more_similar_than_unrelated_texts():
    embedder = HashingBagOfWordsEmbedder(dimension=256)
    anchor = "bids for connection are small moments of reaching out to a partner"
    similar = "reaching out to a partner with small bids for connection"
    unrelated = "quarterly tax filing deadlines for small businesses"

    anchor_vec, similar_vec, unrelated_vec = embedder.embed([anchor, similar, unrelated])

    assert _cosine(anchor_vec, similar_vec) > _cosine(anchor_vec, unrelated_vec)


def test_vectors_are_unit_normalized():
    embedder = HashingBagOfWordsEmbedder(dimension=128)
    (vec,) = embedder.embed(["some sample text with several different words"])
    norm = math.sqrt(sum(v * v for v in vec))
    assert math.isclose(norm, 1.0, rel_tol=1e-6)
