import httpx

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"


class LLMClient:
    """Thin wrapper over the Claude Messages API (direct HTTP, no SDK dependency)."""

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def complete(self, system: str, user: str, max_tokens: int = 500) -> str:
        response = httpx.post(
            _ANTHROPIC_API_URL,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": _ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json={
                "model": self._model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        content = response.json()["content"]
        return "".join(block["text"] for block in content if block.get("type") == "text")
