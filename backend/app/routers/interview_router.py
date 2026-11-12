from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.connection import get_db
from app.models.interview import AnswerEvaluation, CandidateAnswer, InterviewQuestion, InterviewSession
from app.schemas.interview_schema import (
    EvaluationResponse,
    InterviewAnswerRequest,
    InterviewResponse,
    InterviewStartRequest,
    QuestionResponse,
)
from app.services.interview_service import InterviewService, InterviewServiceError
from app.services.llm_service import (
    GeminiLLMService,
    LLMConfigurationError,
    LLMServiceError,
    get_llm_service,
)

router = APIRouter(prefix=f"{settings.api_v1_prefix}/interviews", tags=["interviews"])


def get_interview_service() -> InterviewService:
    return InterviewService()


def _question_response(db: Session, question: InterviewQuestion | None) -> QuestionResponse | None:
    if question is None:
        return None
    answer = db.query(CandidateAnswer).filter_by(question_id=question.id).one_or_none()
    evaluation = (
        db.query(AnswerEvaluation).filter_by(answer_id=answer.id).one_or_none()
        if answer else None
    )
    return QuestionResponse(
        id=question.id,
        sequence=question.sequence,
        question=question.question,
        question_type=question.question_type,
        status=question.status,
        answer=answer.answer if answer else None,
        evaluation=EvaluationResponse.model_validate(evaluation, from_attributes=True) if evaluation else None,
    )


def _response(db: Session, session: InterviewSession) -> InterviewResponse:
    questions = db.query(InterviewQuestion).filter_by(session_id=session.id).order_by(
        InterviewQuestion.sequence
    ).all()
    current = next((item for item in questions if item.sequence == session.current_question_index), None)
    return InterviewResponse(
        id=session.id, resume_id=session.resume_id, job_id=session.job_id,
        interview_type=session.interview_type, difficulty=session.difficulty,
        question_count=session.question_count, duration_minutes=session.duration_minutes,
        status=session.status, current_question_index=session.current_question_index,
        question=_question_response(db, current),
        questions=[_question_response(db, item) for item in questions],
        summary=session.summary, created_at=session.created_at, updated_at=session.updated_at,
    )


def _error(error: Exception) -> HTTPException:
    if isinstance(error, LookupError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, (LLMConfigurationError, InterviewServiceError)):
        return HTTPException(status_code=503, detail=str(error))
    if isinstance(error, LLMServiceError):
        return HTTPException(status_code=502, detail=str(error))
    return HTTPException(status_code=409, detail=str(error))


@router.post("/start", response_model=InterviewResponse, status_code=201)
def start_interview(
    payload: InterviewStartRequest,
    db: Session = Depends(get_db),
    service: InterviewService = Depends(get_interview_service),
    llm_service: GeminiLLMService = Depends(get_llm_service),
) -> InterviewResponse:
    try:
        return _response(db, service.start(db, payload, llm_service))
    except Exception as error:
        raise _error(error) from error


@router.get("/{interview_id}", response_model=InterviewResponse)
def get_interview(interview_id: int, db: Session = Depends(get_db)) -> InterviewResponse:
    session = db.get(InterviewSession, interview_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview not found.")
    return _response(db, session)


@router.post("/{interview_id}/answer", response_model=InterviewResponse)
def submit_answer(
    interview_id: int,
    payload: InterviewAnswerRequest,
    db: Session = Depends(get_db),
    service: InterviewService = Depends(get_interview_service),
    llm_service: GeminiLLMService = Depends(get_llm_service),
) -> InterviewResponse:
    try:
        session, _, _ = service.answer(db, interview_id, payload.answer, llm_service)
        return _response(db, session)
    except Exception as error:
        raise _error(error) from error


@router.post("/{interview_id}/next-question", response_model=InterviewResponse)
def next_question(interview_id: int, db: Session = Depends(get_db)) -> InterviewResponse:
    session = db.get(InterviewSession, interview_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview not found.")
    if session.status == "ready_to_complete":
        raise HTTPException(status_code=409, detail="All configured questions are complete.")
    return _response(db, session)


@router.post("/{interview_id}/complete", response_model=InterviewResponse)
def complete_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    service: InterviewService = Depends(get_interview_service),
    llm_service: GeminiLLMService = Depends(get_llm_service),
) -> InterviewResponse:
    try:
        return _response(db, service.complete(db, interview_id, llm_service))
    except Exception as error:
        raise _error(error) from error
