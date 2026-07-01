from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.consent import CURRENT_NOTICE_VERSION, OTHER_PARTY_NOTICE_TEXT
from app.db.session import get_db
from app.models.consent import ConsentRecord
from app.models.user import User
from app.schemas.consent import ConsentCreateRequest, ConsentRead

router = APIRouter(prefix="/consent", tags=["consent"])


@router.get("/notice")
def get_notice() -> dict[str, str]:
    return {"notice_version": CURRENT_NOTICE_VERSION, "notice_text": OTHER_PARTY_NOTICE_TEXT}


@router.post("", response_model=ConsentRead, status_code=status.HTTP_201_CREATED)
def record_consent(
    payload: ConsentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConsentRecord:
    if not payload.is_adult_confirmed or not payload.other_party_notice_ack:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both 18+ confirmation and the other-party-notice acknowledgement are required",
        )

    consent = ConsentRecord(
        user_id=current_user.id,
        jurisdiction=payload.jurisdiction,
        is_adult_confirmed=payload.is_adult_confirmed,
        other_party_notice_ack=payload.other_party_notice_ack,
        notice_version=CURRENT_NOTICE_VERSION,
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent
