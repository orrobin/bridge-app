import hashlib
import uuid

from sqlalchemy.orm import Session

from app.agents.safety import SafetyClassifier, SafetyDecision, get_safety_classifier
from app.models.audit import AuditLogEntry


class SafetyAgent:
    """Wraps a SafetyClassifier with the audit-log write every decision requires
    (SAD Phase 4.2: Safety runs pre and post, every decision is logged)."""

    def __init__(self, classifier: SafetyClassifier | None = None) -> None:
        self._classifier = classifier or get_safety_classifier()

    def _log(
        self,
        db: Session,
        user_id: uuid.UUID | None,
        action: str,
        text: str,
        decision: SafetyDecision,
    ) -> None:
        db.add(
            AuditLogEntry(
                user_id=user_id,
                actor="safety_agent",
                action=action,
                decision=decision.decision,
                reason=decision.reason,
                input_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            )
        )
        db.commit()

    def pre_screen(self, db: Session, user_id: uuid.UUID, conversation_text: str) -> SafetyDecision:
        decision = self._classifier.classify_pre_screen(conversation_text)
        self._log(db, user_id, "pre_screen", conversation_text, decision)
        return decision

    def post_gate(self, db: Session, user_id: uuid.UUID, draft_reply: str) -> SafetyDecision:
        decision = self._classifier.classify_post_gate(draft_reply)
        self._log(db, user_id, "post_gate", draft_reply, decision)
        return decision
