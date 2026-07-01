import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class UploadedChatData(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Redacted, short-TTL target-party conversation data (SAD Phase 6.1/6.2).

    Only ever stores redacted turns -- raw uploaded text is redacted before this
    row is created and is never persisted. `expires_at` enforces the short TTL;
    see app.core.retention.purge_expired_uploads for the cleanup job.
    """

    __tablename__ = "uploaded_chat_data"

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversation_threads.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    redacted_turns: Mapped[list] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
