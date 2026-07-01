import json
from typing import Protocol

from app.core.config import Settings, get_settings
from app.core.llm_client import LLMClient
from app.schemas.reasoning import Hypothesis

RetrievedChunk = tuple[str, str]  # (source_id, content)


class AnalystProvider(Protocol):
    def analyze(
        self, conversation_text: str, retrieved_context: list[RetrievedChunk]
    ) -> list[Hypothesis]: ...


class HeuristicAnalystProvider:
    """Deterministic placeholder (no LLM credits available -- see TASKS.md T6.1/T7.2).

    Produces simple, always-hedged, always-cited hypotheses from surface signals
    (turn-taking balance, question-asking). This is intentionally conservative:
    confidence never exceeds "medium" and every claim carries counter-evidence,
    matching the "no scores-as-truth" rule. ClaudeAnalystProvider below is the
    real implementation, ready to swap in once Anthropic API credits exist.
    """

    def analyze(
        self, conversation_text: str, retrieved_context: list[RetrievedChunk]
    ) -> list[Hypothesis]:
        citations = [source_id for source_id, _ in retrieved_context]
        lines = [line for line in conversation_text.splitlines() if line.strip()]
        question_lines = [line for line in lines if "?" in line]

        hypotheses = [
            Hypothesis(
                claim=(
                    "There's a reasonably even back-and-forth in this conversation, which is "
                    "generally a sign of mutual engagement."
                    if len(lines) >= 2
                    else "There isn't much conversation yet to draw a pattern from."
                ),
                confidence="low",
                counter_evidence=(
                    "Turn count alone doesn't capture tone, timing, or who initiated each "
                    "topic -- a short thread can still be warm, and a long one can be flat."
                ),
                citations=citations[:1],
            )
        ]

        if question_lines:
            hypotheses.append(
                Hypothesis(
                    claim=(
                        "Questions are being asked in this thread, which is one marker of "
                        "active listening rather than one-sided messaging."
                    ),
                    confidence="low",
                    counter_evidence=(
                        "Asking questions doesn't guarantee the replies actually engage with "
                        "what the other person said -- that requires reading the content, not "
                        "just counting question marks."
                    ),
                    citations=citations[:1],
                )
            )

        return hypotheses


_ANALYST_SYSTEM_PROMPT = """\
You are the Conversation Analyst in a dating-communication coaching app. Given a
redacted conversation and grounding context from a knowledge base, produce 2-3
hypotheses about communication patterns/strengths. Each hypothesis MUST include:
a claim, a confidence level of exactly "low", "medium", or "high" (never higher
certainty than the evidence supports -- this is text-only inference, which is
low-validity), explicit counter-evidence/an alternative explanation, and
citations (source ids) from the provided context. Never state a claim as a bare
numeric score or as certain fact. Respond with ONLY a JSON array of objects with
keys: claim, confidence, counter_evidence, citations (array of strings).
"""


class ClaudeAnalystProvider:
    """Real LLM-based Analyst. Not the default yet -- see HeuristicAnalystProvider."""

    def __init__(self, client: LLMClient) -> None:
        self._client = client

    def analyze(
        self, conversation_text: str, retrieved_context: list[RetrievedChunk]
    ) -> list[Hypothesis]:
        context_block = "\n\n".join(f"[{sid}] {content}" for sid, content in retrieved_context)
        user_message = f"Conversation:\n{conversation_text}\n\nContext:\n{context_block}"
        raw = self._client.complete(_ANALYST_SYSTEM_PROMPT, user_message, max_tokens=1000)
        return [Hypothesis(**item) for item in json.loads(raw)]


def get_analyst_provider(settings: Settings | None = None) -> AnalystProvider:
    settings = settings or get_settings()
    if settings.use_llm_agents and settings.anthropic_api_key:
        client = LLMClient(api_key=settings.anthropic_api_key, model=settings.generation_model)
        return ClaudeAnalystProvider(client)
    return HeuristicAnalystProvider()
