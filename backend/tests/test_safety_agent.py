from app.agents.safety_agent import SafetyAgent
from app.db.session import SessionLocal
from app.models.audit import AuditLogEntry
from app.models.user import User
from tests.conftest import unique_email


def test_every_decision_is_written_to_the_audit_log():
    db = SessionLocal()
    try:
        user = User(email=unique_email(), hashed_password="not-a-real-hash")
        db.add(user)
        db.flush()

        agent = SafetyAgent()
        pre_decision = agent.pre_screen(db, user.id, "SPEAKER_1: hey, how's it going?")
        post_decision = agent.post_gate(db, user.id, "I had a great time talking with you!")

        entries = (
            db.query(AuditLogEntry)
            .filter(AuditLogEntry.user_id == user.id)
            .order_by(AuditLogEntry.created_at)
            .all()
        )
        assert len(entries) == 2

        assert entries[0].actor == "safety_agent"
        assert entries[0].action == "pre_screen"
        assert entries[0].decision == pre_decision.decision
        assert entries[0].reason == pre_decision.reason
        assert entries[0].input_hash

        assert entries[1].action == "post_gate"
        assert entries[1].decision == post_decision.decision
        assert entries[1].reason == post_decision.reason
    finally:
        db.query(AuditLogEntry).filter(AuditLogEntry.user_id == user.id).delete(
            synchronize_session=False
        )
        db.query(User).filter(User.id == user.id).delete(synchronize_session=False)
        db.commit()
        db.close()


def test_blocked_pre_screen_is_logged_as_block_decision():
    db = SessionLocal()
    try:
        user = User(email=unique_email(), hashed_password="not-a-real-hash")
        db.add(user)
        db.flush()

        agent = SafetyAgent()
        decision = agent.pre_screen(db, user.id, "SPEAKER_1: reply to me right now or else")
        # "block" from the rule-based floor, or "escalate" if the LLM (when the
        # ensemble is active) reads it as more severe -- both are a correct stop,
        # and which one wins isn't deterministic across LLM calls.
        assert decision.decision in ("block", "escalate")

        entry = (
            db.query(AuditLogEntry).filter(AuditLogEntry.user_id == user.id).one()
        )
        assert entry.decision in ("block", "escalate")
    finally:
        db.query(AuditLogEntry).filter(AuditLogEntry.user_id == user.id).delete(
            synchronize_session=False
        )
        db.query(User).filter(User.id == user.id).delete(synchronize_session=False)
        db.commit()
        db.close()
