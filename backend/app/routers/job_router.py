from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.connection import get_db
from app.models.job_description import JobDescription
from app.models.job_match import JobMatch
from app.schemas.job_description_schema import (
    JobDescriptionAnalysis,
    JobDescriptionCreate,
    JobDescriptionResponse,
)
from app.schemas.job_matching_schema import JobMatchData, JobMatchResponse
from app.services.job_description_service import analyze_job_description
from app.services.job_matching_service import match_resume_to_job
from app.services.llm_service import (
    GeminiLLMService,
    LLMConfigurationError,
    LLMServiceError,
    get_llm_service,
)

router = APIRouter(prefix=f"{settings.api_v1_prefix}/jobs", tags=["jobs"])


def _job_response(job: JobDescription) -> JobDescriptionResponse:
    return JobDescriptionResponse(
        id=job.id,
        description=job.description,
        created_at=job.created_at,
        updated_at=job.updated_at,
        **job.analysis,
    )


def _match_response(match: JobMatch) -> JobMatchResponse:
    data = JobMatchData.model_validate(match.result)
    return JobMatchResponse(
        id=match.id,
        job_id=match.job_id,
        resume_id=match.resume_id,
        created_at=match.created_at,
        updated_at=match.updated_at,
        **data.model_dump(),
    )


@router.post("/analyze", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
def analyze_job(
    payload: JobDescriptionCreate,
    db: Session = Depends(get_db),
    llm_service: GeminiLLMService = Depends(get_llm_service),
) -> JobDescriptionResponse:
    try:
        return _job_response(analyze_job_description(db, payload.description, llm_service))
    except LLMConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except LLMServiceError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database unavailable.") from error


@router.get("/{job_id}", response_model=JobDescriptionResponse)
def get_job(job_id: int, db: Session = Depends(get_db)) -> JobDescriptionResponse:
    job = db.get(JobDescription, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job description not found.")
    return _job_response(job)


@router.post("/{job_id}/match/{resume_id}", response_model=JobMatchResponse)
def match_job(
    job_id: int,
    resume_id: int,
    db: Session = Depends(get_db),
    llm_service: GeminiLLMService = Depends(get_llm_service),
) -> JobMatchResponse:
    try:
        return _match_response(match_resume_to_job(db, job_id, resume_id, llm_service))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except LLMConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except LLMServiceError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database unavailable.") from error
