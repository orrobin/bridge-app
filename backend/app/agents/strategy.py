import re
from typing import Protocol

from app.core.config import Settings, get_settings
from app.core.llm_client import LLMClient
from app.schemas.reasoning import StrategyOption, StrategyOutput

RetrievedChunk = tuple[str, str]  # (source_id, content)

# Explicit disinterest / a "no" -- the hard rule (SAD Phase 1.5/ADR): never offer
# a "keep pursuing" option once this is detected.
_DISINTEREST_PATTERNS = [
    r"\bnot interested\b",
    r"\bdon'?t think this is (a match|going to work)\b",
    r"\bstop (texting|messaging|contacting) me\b",
    r"\bi'?m not looking for (this|anything) right now\b",
    r"\bplease (stop|leave me alone)\b",
    r"\bnot feeling (a connection|this)\b",
]

# Mutual, positive signals -- safe to suggest meeting up.
_MUTUAL_SIGNAL_PATTERNS = [
    r"\bwould love to (meet|hang out|grab)\b",
    r"\blet'?s (meet up|hang out|grab)\b",
    r"\bi'?m free (this|next) weekend\b",
    r"\bcan'?t wait to (meet|see) you\b",
]


class StrategyProvider(Protocol):
    def generate(
        self, conversation_text: str, retrieved_context: list[RetrievedChunk]
    ) -> StrategyOutput: ...


class HeuristicStrategyProvider:
    """Deterministic placeholder (no LLM credits -- see TASKS.md T6.1/T7.4).

    The disinterest/mutual-signal detection here is real (regex-based), not a
    stand-in -- what's a placeholder is the quality of the suggested reply
    wording, which a real model (ClaudeStrategyProvider) will do much better.
    The hard safety rule (never suggest pursuing past a detected "no") is
    enforced regardless of which provider is active.
    """

    def generate(
        self, conversation_text: str, retrieved_context: list[RetrievedChunk]
    ) -> StrategyOutput:
        text = conversation_text.lower()
        disinterest_detected = any(re.search(p, text) for p in _DISINTEREST_PATTERNS)
        mutual_signals_detected = any(re.search(p, text) for p in _MUTUAL_SIGNAL_PATTERNS)
        citations = [source_id for source_id, _ in retrieved_context]

        if disinterest_detected:
            options = [
                StrategyOption(
                    message=(
                        "Thanks for being upfront with me -- I appreciate it. Wishing you well!"
                    ),
                    reasoning=(
                        "A clear signal of disinterest is worth accepting gracefully rather than "
                        "pushing back on or trying to negotiate."
                    ),
                    citations=citations[:1],
                ),
                StrategyOption(
                    message="No worries at all, take care!",
                    reasoning="A short, low-pressure, respectful close.",
                    citations=citations[:1],
                ),
            ]
            return StrategyOutput(
                options=options,
                disinterest_detected=True,
                mutual_signals_detected=mutual_signals_detected,
            )

        options = [
            StrategyOption(
                message="That's really interesting -- what got you into that?",
                reasoning="An authentic, curious follow-up that builds on what they said.",
                citations=citations[:1],
            ),
            StrategyOption(
                message="Ha, I can relate to that more than you'd think.",
                reasoning="A warm, genuine response that shares a little without oversharing.",
                citations=citations[:1],
            ),
        ]
        if mutual_signals_detected:
            options.append(
                StrategyOption(
                    message="I'd love to grab coffee sometime this week if you're up for it!",
                    reasoning=(
                        "Signals from both sides seem mutual and positive, so suggesting a "
                        "low-pressure meetup is reasonable timing."
                    ),
                    citations=citations[:1],
                    is_meeting_suggestion=True,
                )
            )

        return StrategyOutput(
            options=options,
            disinterest_detected=False,
            mutual_signals_detected=mutual_signals_detected,
        )


_STRATEGY_SYSTEM_PROMPT = """\
You are the Dating Strategy agent in a dating-communication coaching app. Given
a redacted conversation and grounding context, produce 2-3 authentic reply
options in the user's own voice, each with reasoning and citations. HARD RULE:
if the other person has expressed disinterest or a "no", you MUST NOT offer any
option that pursues, argues, or pressures -- only graceful, respectful
close-out options. If signals are clearly mutual and positive, one option may
suggest meeting up (mark is_meeting_suggestion true). Respond with ONLY a JSON
object: {"options": [{"message":..., "reasoning":..., "citations":[...],
"is_meeting_suggestion": bool}], "disinterest_detected": bool,
"mutual_signals_detected": bool}.
"""


class ClaudeStrategyProvider:
    """Real LLM-based Strategy agent. Not the default yet -- see HeuristicStrategyProvider."""

    def __init__(self, client: LLMClient) -> None:
        self._client = client

    def generate(
        self, conversation_text: str, retrieved_context: list[RetrievedChunk]
    ) -> StrategyOutput:
        context_block = "\n\n".join(f"[{sid}] {content}" for sid, content in retrieved_context)
        user_message = f"Conversation:\n{conversation_text}\n\nContext:\n{context_block}"
        parsed = self._client.complete_json(
            _STRATEGY_SYSTEM_PROMPT, user_message, max_tokens=1200
        )
        return StrategyOutput(**parsed)


def get_strategy_provider(settings: Settings | None = None) -> StrategyProvider:
    settings = settings or get_settings()
    if settings.use_llm_agents and settings.anthropic_api_key:
        client = LLMClient(api_key=settings.anthropic_api_key, model=settings.generation_model)
        return ClaudeStrategyProvider(client)
    return HeuristicStrategyProvider()
