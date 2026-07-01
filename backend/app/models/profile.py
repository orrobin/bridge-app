import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserProfile(UUIDPrimaryKeyMixin, Base):
    """The durable, user-only behavioral profile (SAD Phase 6.1).

    Never stores a profile of the other party in a conversation -- only
    distilled, consented signals about the user themselves.
    """

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    attachment_style_hints: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    recurring_patterns: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    goals: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    voice_profile: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="profile")
