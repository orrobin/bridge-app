import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.consent import CURRENT_NOTICE_VERSION
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.consent import ConsentRecord
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_error

    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_error

    user = db.get(User, uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_consent(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConsentRecord:
    """Gate for any endpoint that touches a conversation upload/analysis.

    Requires a consent record for the current notice version with both the
    18+ confirmation and the other-party-non-consent acknowledgement set.
    """
    consent = (
        db.query(ConsentRecord)
        .filter(
            ConsentRecord.user_id == current_user.id,
            ConsentRecord.notice_version == CURRENT_NOTICE_VERSION,
            ConsentRecord.is_adult_confirmed.is_(True),
            ConsentRecord.other_party_notice_ack.is_(True),
        )
        .order_by(ConsentRecord.consented_at.desc())
        .first()
    )
    if consent is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Consent required before analysis: confirm you are 18+, acknowledge "
                "the other-party-non-consent notice, and record your jurisdiction via "
                "POST /consent."
            ),
        )
    return consent
