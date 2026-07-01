from app.agents.orchestrator import Orchestrator
from app.db.session import SessionLocal
from app.models.audit import AuditLogEntry
from app.models.user import User
from tests.conftest import unique_email


def _fake_retriever(query: str) -> list[tuple[str, str]]:
    return [("bids-for-connection", "Bids for connection are small moments of reaching out.")]


def _cleanup(db, user_id) -> None:
    # SafetyAgent commits internally, so the flushed User row is durable too --
    # can't just rollback, have to delete what was actually written.
    db.query(AuditLogEntry).filter(AuditLogEntry.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
    db.commit()


def test_orchestrator_call_order_for_a_clean_conversation():
    db = SessionLocal()
    try:
        user = User(email=unique_email(), hashed_password="not-a-real-hash")
        db.add(user)
        db.flush()

        orchestrator = Orchestrator(retrieve_fn=_fake_retriever)
        result = orchestrator.run(
            db,
            user.id,
            conversation_text="SPEAKER_1: hey how's it going?\nSPEAKER_2: good, you?",
            retrieval_query="how's it going",
        )

        assert result.trace == [
            "safety_pre_screen",
            "retrieval",
            "analyst",
            "eq",
            "strategy",
            "safety_post_gate",
            "done",
        ]
        assert result.safety_stopped is False
        assert len(result.hypotheses) >= 1
        assert len(result.emotional_reads) >= 1
        assert result.strategy is not None
        assert len(result.strategy.options) >= 1
    finally:
        _cleanup(db, user.id)
        db.close()


def test_orchestrator_stops_early_on_red_flag_and_skips_later_steps():
    db = SessionLocal()
    try:
        user = User(email=unique_email(), hashed_password="not-a-real-hash")
        db.add(user)
        db.flush()

        orchestrator = Orchestrator(retrieve_fn=_fake_retriever)
        result = orchestrator.run(
            db,
            user.id,
            conversation_text="SPEAKER_1: reply to me right now or else",
            retrieval_query="anything",
        )

        assert result.trace == ["safety_pre_screen"]
        assert result.safety_stopped is True
        assert result.safety_decision is not None
        # "block" from the rule-based floor or "escalate" if the LLM (when enabled
        # via the ensemble) reads it as more severe -- both correctly stop the
        # pipeline, which is the property this test actually cares about.
        assert result.safety_decision.decision in ("block", "escalate")
        assert result.hypotheses == []
        assert result.strategy is None
    finally:
        _cleanup(db, user.id)
        db.close()


def test_orchestrator_post_gate_filters_manipulative_strategy_options():
    class ManipulativeStrategyStub:
        def generate(self, conversation_text, retrieved_context):
            from app.schemas.reasoning import StrategyOption, StrategyOutput

            return StrategyOutput(
                options=[
                    StrategyOption(message="I had a great time chatting with you!", reasoning="ok"),
                    StrategyOption(message="You're my soulmate, I just know it.", reasoning="bad"),
                ],
                disinterest_detected=False,
                mutual_signals_detected=False,
            )

    db = SessionLocal()
    try:
        user = User(email=unique_email(), hashed_password="not-a-real-hash")
        db.add(user)
        db.flush()

        orchestrator = Orchestrator(
            retrieve_fn=_fake_retriever, strategy=ManipulativeStrategyStub()
        )
        result = orchestrator.run(
            db,
            user.id,
            conversation_text="SPEAKER_1: hey!\nSPEAKER_2: hi!",
            retrieval_query="anything",
        )

        assert len(result.strategy.options) == 1
        assert "soulmate" not in result.strategy.options[0].message.lower()
    finally:
        _cleanup(db, user.id)
        db.close()
