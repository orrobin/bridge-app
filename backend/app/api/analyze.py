from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.orchestrator import Orchestrator, RetrievedChunk
from app.api.deps import get_current_user, require_consent
from app.core.safety_resources import SAFETY_STOP_MESSAGE
from app.db.session import get_db
from app.models.consent import ConsentRecord
from app.models.upload import UploadedChatData
from app.models.user import User
from app.rag.embeddings import get_embedding_provider
from app.rag.retrieval import hybrid_search
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse

router = APIRouter(tags=["analyze"])


def _turns_to_text(redacted_turns: list[dict]) -> str:
    return "\n".join(f"{turn['speaker']}: {turn['text']}" for turn in redacted_turns)


def _make_retrieve_fn(db: Session):
    embedder = get_embedding_provider()

    def retrieve(query: str) -> list[RetrievedChunk]:
        (query_embedding,) = embedder.embed([query])
        chunks = hybrid_search(db, query, query_embedding, top_k=3)
        return [(chunk.source_id, chunk.content) for chunk in chunks]

    return retrieve


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    payload: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    _consent: ConsentRecord = Depends(require_consent),
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    upload = (
        db.query(UploadedChatData)
        .filter(
            UploadedChatData.thread_id == payload.thread_id,
            UploadedChatData.user_id == current_user.id,
        )
        .order_by(UploadedChatData.created_at.desc())
        .first()
    )
    if upload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No uploaded chat found for this thread_id -- upload one via POST /upload first",
        )

    conversation_text = _turns_to_text(upload.redacted_turns)

    orchestrator = Orchestrator(retrieve_fn=_make_retrieve_fn(db))
    result = orchestrator.run(
        db, current_user.id, conversation_text, retrieval_query=conversation_text
    )

    if result.safety_stopped:
        return AnalyzeResponse(safety_stopped=True, safety_message=SAFETY_STOP_MESSAGE)

    return AnalyzeResponse(
        safety_stopped=False,
        hypotheses=result.hypotheses,
        emotional_reads=result.emotional_reads,
        strategy=result.strategy,
    )
