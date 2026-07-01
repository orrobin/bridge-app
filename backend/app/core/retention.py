from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.upload import UploadedChatData

# SAD Phase 6.1/6.2: target-party data is short-TTL, never embedded long-term.
TARGET_DATA_TTL_DAYS = 30


def compute_expiry(now: datetime | None = None) -> datetime:
    base = now or datetime.now(UTC)
    return base + timedelta(days=TARGET_DATA_TTL_DAYS)


def purge_expired_uploads(db: Session, now: datetime | None = None) -> int:
    """Delete uploaded target-party data past its TTL. Returns the number of rows purged."""
    cutoff = now or datetime.now(UTC)
    deleted = (
        db.query(UploadedChatData)
        .filter(UploadedChatData.expires_at < cutoff)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted
