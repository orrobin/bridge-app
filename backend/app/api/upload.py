from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_consent
from app.core.chat_parser import ChatParseError, parse_chat_export
from app.core.redaction import redact_turns
from app.core.retention import compute_expiry
from app.db.session import get_db
from app.models.consent import ConsentRecord
from app.models.thread import ConversationThread
from app.models.upload import UploadedChatData
from app.models.user import User
from app.schemas.upload import ChatUploadRequest, ChatUploadResponse

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=ChatUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_chat(
    payload: ChatUploadRequest,
    current_user: User = Depends(get_current_user),
    _consent: ConsentRecord = Depends(require_consent),
    db: Session = Depends(get_db),
) -> ChatUploadResponse:
    try:
        turns = parse_chat_export(payload.raw_text)
    except ChatParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    redacted = redact_turns(turns)

    thread = ConversationThread(user_id=current_user.id, label=payload.thread_label or "Untitled")
    db.add(thread)
    db.flush()  # assign thread.id without committing yet

    upload = UploadedChatData(
        thread_id=thread.id,
        user_id=current_user.id,
        redacted_turns=redacted,
        expires_at=compute_expiry(),
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    return ChatUploadResponse(
        id=upload.id, thread_id=thread.id, turns=redacted, expires_at=upload.expires_at
    )
