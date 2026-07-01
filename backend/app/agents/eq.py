import json
import re
from typing import Protocol

from app.core.config import Settings, get_settings
from app.core.llm_client import LLMClient
from app.schemas.reasoning import EmotionalRead

_POSITIVE_WORDS = re.compile(
    r"\b(haha|lol|excited|love|great|awesome|fun|glad|happy|looking forward)\b", re.IGNORECASE
)
_SHORT_REPLY_PATTERN = re.compile(r"^(ok|okay|sure|k|fine)\.?$", re.IGNORECASE)


class EQProvider(Protocol):
    def analyze(self, conversation_text: str) -> list[EmotionalRead]: ...


class HeuristicEQProvider:
    """Deterministic placeholder (no LLM credits -- see TASKS.md T6.1/T7.3).

    Every read is paired with a required counter_read, enforced by the
    EmotionalRead schema (not optional), regardless of which provider is active.
    ClaudeEQProvider below is the real implementation.
    """

    def analyze(self, conversation_text: str) -> list[EmotionalRead]:
        reads: list[EmotionalRead] = []
        lines = [line for line in conversation_text.splitlines() if line.strip()]

        positive_hits = sum(1 for line in lines if _POSITIVE_WORDS.search(line))
        if positive_hits:
            reads.append(
                EmotionalRead(
                    read=(
                        "Some messages use warm, enthusiastic language, which could suggest "
                        "genuine interest or comfort in the conversation."
                    ),
                    confidence="low",
                    counter_read=(
                        "Could also just be someone's normal texting style regardless of "
                        "how they feel about this specific conversation."
                    ),
                )
            )

        short_reply_hits = sum(
            1 for line in lines if _SHORT_REPLY_PATTERN.search(line.split(":")[-1].strip())
        )
        if short_reply_hits:
            reads.append(
                EmotionalRead(
                    read=(
                        "There are some very short, low-effort-looking replies in this thread, "
                        "which could suggest reduced engagement."
                    ),
                    confidence="low",
                    counter_read=(
                        "Could also just mean they were busy, on their phone briefly, or are "
                        "naturally a low-word-count texter -- short replies alone aren't reliable "
                        "evidence of disinterest."
                    ),
                )
            )

        if not reads:
            reads.append(
                EmotionalRead(
                    read="No strong emotional signal stands out either way in this excerpt.",
                    confidence="low",
                    counter_read=(
                        "A short or neutral-sounding excerpt can still sit inside a warm "
                        "overall conversation -- this read is about this excerpt alone, not "
                        "the whole thread."
                    ),
                )
            )

        return reads


_EQ_SYSTEM_PROMPT = """\
You are the Emotional Intelligence agent in a dating-communication coaching app.
Given a redacted conversation, produce 1-3 possible emotional reads. Text-only
inference of emotion is low-validity, so EVERY read MUST include a counter_read
(a plausible alternative explanation) -- never emit a read without one. Respond
with ONLY a JSON array of objects with keys: read, confidence (exactly "low",
"medium", or "high"), counter_read.
"""


class ClaudeEQProvider:
    """Real LLM-based EQ agent. Not the default yet -- see HeuristicEQProvider."""

    def __init__(self, client: LLMClient) -> None:
        self._client = client

    def analyze(self, conversation_text: str) -> list[EmotionalRead]:
        raw = self._client.complete(_EQ_SYSTEM_PROMPT, conversation_text, max_tokens=800)
        return [EmotionalRead(**item) for item in json.loads(raw)]


def get_eq_provider(settings: Settings | None = None) -> EQProvider:
    settings = settings or get_settings()
    if settings.use_llm_agents and settings.anthropic_api_key:
        client = LLMClient(api_key=settings.anthropic_api_key, model=settings.generation_model)
        return ClaudeEQProvider(client)
    return HeuristicEQProvider()
