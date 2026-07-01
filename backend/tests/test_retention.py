from datetime import UTC, datetime, timedelta

from app.core.retention import purge_expired_uploads
from app.db.session import SessionLocal
from app.models.thread import ConversationThread
from app.models.upload import UploadedChatData
from app.models.user import User
from tests.conftest import unique_email


def test_purge_expired_uploads_deletes_only_expired_rows():
    db = SessionLocal()
    try:
        user = User(email=unique_email(), hashed_password="not-a-real-hash")
        db.add(user)
        db.flush()

        thread = ConversationThread(user_id=user.id, label="Untitled")
        db.add(thread)
        db.flush()

        expired = UploadedChatData(
            thread_id=thread.id,
            user_id=user.id,
            redacted_turns=[{"speaker": "SPEAKER_1", "text": "hi"}],
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        not_expired = UploadedChatData(
            thread_id=thread.id,
            user_id=user.id,
            redacted_turns=[{"speaker": "SPEAKER_1", "text": "hi"}],
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        db.add_all([expired, not_expired])
        db.commit()
        expired_id, not_expired_id = expired.id, not_expired.id

        deleted_count = purge_expired_uploads(db)
        assert deleted_count >= 1

        remaining_ids = {
            row.id
            for row in db.query(UploadedChatData)
            .filter(UploadedChatData.id.in_([expired_id, not_expired_id]))
            .all()
        }
        assert expired_id not in remaining_ids
        assert not_expired_id in remaining_ids
    finally:
        db.query(UploadedChatData).filter(UploadedChatData.user_id == user.id).delete(
            synchronize_session=False
        )
        db.query(ConversationThread).filter(ConversationThread.user_id == user.id).delete(
            synchronize_session=False
        )
        db.query(User).filter(User.id == user.id).delete(synchronize_session=False)
        db.commit()
        db.close()
