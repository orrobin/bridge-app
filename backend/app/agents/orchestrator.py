import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.agents.analyst import AnalystProvider, RetrievedChunk, get_analyst_provider
from app.agents.eq import EQProvider, get_eq_provider
from app.agents.safety import SafetyDecision
from app.agents.safety_agent import SafetyAgent
from app.agents.strategy import StrategyProvider, get_strategy_provider
from app.schemas.reasoning import EmotionalRead, Hypothesis, StrategyOutput

RetrieveFn = Callable[[str], list[RetrievedChunk]]


@dataclass
class OrchestratorResult:
    trace: list[str] = field(default_factory=list)
    safety_stopped: bool = False
    safety_decision: SafetyDecision | None = None
    hypotheses: list[Hypothesis] = field(default_factory=list)
    emotional_reads: list[EmotionalRead] = field(default_factory=list)
    strategy: StrategyOutput | None = None


class Orchestrator:
    """Deterministic control flow (SAD Phase 4.1): Safety pre -> Analyst + EQ ->
    Strategy -> Safety post (applied to every outgoing option). Every step is
    appended to `trace` so the call order is independently verifiable."""

    def __init__(
        self,
        retrieve_fn: RetrieveFn,
        safety_agent: SafetyAgent | None = None,
        analyst: AnalystProvider | None = None,
        eq: EQProvider | None = None,
        strategy: StrategyProvider | None = None,
    ) -> None:
        self._retrieve_fn = retrieve_fn
        self._safety = safety_agent or SafetyAgent()
        self._analyst = analyst or get_analyst_provider()
        self._eq = eq or get_eq_provider()
        self._strategy = strategy or get_strategy_provider()

    def run(
        self, db: Session, user_id: uuid.UUID, conversation_text: str, retrieval_query: str
    ) -> OrchestratorResult:
        trace: list[str] = []

        trace.append("safety_pre_screen")
        pre_decision = self._safety.pre_screen(db, user_id, conversation_text)
        if pre_decision.decision != "allow":
            return OrchestratorResult(
                trace=trace, safety_stopped=True, safety_decision=pre_decision
            )

        trace.append("retrieval")
        retrieved_context = self._retrieve_fn(retrieval_query)

        trace.append("analyst")
        hypotheses = self._analyst.analyze(conversation_text, retrieved_context)

        trace.append("eq")
        emotional_reads = self._eq.analyze(conversation_text)

        trace.append("strategy")
        strategy_output = self._strategy.generate(conversation_text, retrieved_context)

        trace.append("safety_post_gate")
        allowed_options = []
        for option in strategy_output.options:
            post_decision = self._safety.post_gate(db, user_id, option.message)
            if post_decision.decision == "allow":
                allowed_options.append(option)
        strategy_output.options = allowed_options

        trace.append("done")
        return OrchestratorResult(
            trace=trace,
            safety_stopped=False,
            hypotheses=hypotheses,
            emotional_reads=emotional_reads,
            strategy=strategy_output,
        )
