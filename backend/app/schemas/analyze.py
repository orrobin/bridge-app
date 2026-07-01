import uuid

from pydantic import BaseModel

from app.schemas.reasoning import EmotionalRead, Hypothesis, StrategyOutput


class AnalyzeRequest(BaseModel):
    thread_id: uuid.UUID


class AnalyzeResponse(BaseModel):
    safety_stopped: bool
    safety_message: str | None = None
    hypotheses: list[Hypothesis] = []
    emotional_reads: list[EmotionalRead] = []
    strategy: StrategyOutput | None = None
