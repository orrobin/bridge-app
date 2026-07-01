from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.consent import ConsentRecord
    from app.models.profile import UserProfile
    from app.models.thread import ConversationThread


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    consent_records: Mapped[list["ConsentRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    threads: Mapped[list["ConversationThread"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    profile: Mapped["UserProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
