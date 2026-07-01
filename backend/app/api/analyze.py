from fastapi import APIRouter, Depends

from app.api.deps import require_consent
from app.models.consent import ConsentRecord

router = APIRouter(tags=["analyze"])


@router.post("/analyze")
def analyze(consent: ConsentRecord = Depends(require_consent)) -> dict[str, str]:
    """Placeholder for the full upload -> redact -> orchestrate pipeline (Epic 3, 6-8)."""
    return {"status": "not_implemented"}
