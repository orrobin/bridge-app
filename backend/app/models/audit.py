import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AuditLogEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tamper-evident-in-intent log of every Safety & Ethics agent decision (SAD Phase 4.2/10.2)."""

    __tablename__ = "audit_log_entries"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "safety_agent"
    action: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "pre_screen"
    decision: Mapped[str] = mapped_column(String(32), nullable=False)  # allow|block|escalate
    reason: Mapped[str] = mapped_column(String(1024), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    extra: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
