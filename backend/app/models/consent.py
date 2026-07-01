import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class ConsentRecord(UUIDPrimaryKeyMixin, Base):
    """A recorded, timestamped consent event. Required before /analyze accepts a request.

    Captures 18+ confirmation, jurisdiction, and acknowledgement of the
    other-party-non-consent notice (SAD Phase 5.1) -- never inferred, always explicit.
    """

    __tablename__ = "consent_records"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    jurisdiction: Mapped[str] = mapped_column(String(64), nullable=False)
    is_adult_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    other_party_notice_ack: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notice_version: Mapped[str] = mapped_column(String(32), nullable=False)
    consented_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="consent_records")
