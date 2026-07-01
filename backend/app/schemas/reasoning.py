from pydantic import BaseModel, Field


class Hypothesis(BaseModel):
    """A confidence-banded claim about the conversation -- never a bare score (SAD ADR-6)."""

    claim: str
    confidence: str = Field(pattern="^(low|medium|high)$")
    counter_evidence: str
    citations: list[str] = Field(default_factory=list)


class EmotionalRead(BaseModel):
    """An emotional-read hypothesis. `counter_read` is required, not optional --
    every read must be paired with a plausible alternative (SAD Phase 4.2)."""

    read: str
    confidence: str = Field(pattern="^(low|medium|high)$")
    counter_read: str


class StrategyOption(BaseModel):
    message: str
    reasoning: str
    citations: list[str] = Field(default_factory=list)
    is_meeting_suggestion: bool = False


class StrategyOutput(BaseModel):
    options: list[StrategyOption]
    disinterest_detected: bool
    mutual_signals_detected: bool
