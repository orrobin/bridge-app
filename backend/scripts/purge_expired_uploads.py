"""Cleanup job: delete uploaded_chat_data rows past their TTL (SAD Phase 6.3).

Intended to run on a schedule (e.g. daily cron / scheduled task):

    python -m scripts.purge_expired_uploads
"""

from app.core.retention import purge_expired_uploads
from app.db.session import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        deleted = purge_expired_uploads(db)
        print(f"Purged {deleted} expired uploaded_chat_data row(s)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
