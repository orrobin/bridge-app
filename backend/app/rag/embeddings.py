import hashlib
import math
import re
from typing import Protocol

import httpx

from app.core.config import Settings, get_settings

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class EmbeddingProvider(Protocol):
    dimension: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashingBagOfWordsEmbedder:
    """Deterministic, dependency-free placeholder embedder (SAD Phase 8.2 notes this is
    swappable for a real hosted/self-hosted model).

    Uses the classic feature-hashing trick: each token is hashed into one of
    `dimension` buckets and accumulated, then L2-normalized. Unlike a purely
    random mock, this preserves genuine word-overlap similarity, so retrieval
    tests (e.g. hybrid vs. vector-only ranking) are meaningful even without a
    trained model. No network access or API key required.
    """

    def __init__(self, dimension: int = 1536) -> None:
        self.dimension = dimension

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in _TOKEN_RE.findall(text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0.0:
            return vector
        return [v / norm for v in vector]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]


class OpenAIEmbedder:
    """Real hosted embedder. Wired up but only exercised once OPENAI_API_KEY is set."""

    def __init__(self, api_key: str, model: str, dimension: int = 1536) -> None:
        self._api_key = api_key
        self._model = model
        self.dimension = dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"model": self._model, "input": texts},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()["data"]
        return [item["embedding"] for item in sorted(data, key=lambda d: d["index"])]


def get_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    settings = settings or get_settings()
    if settings.openai_api_key:
        return OpenAIEmbedder(api_key=settings.openai_api_key, model=settings.embedding_model)
    return HashingBagOfWordsEmbedder()
