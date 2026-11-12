from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.connection import get_db
from app.schemas.resume_analysis_schema import ResumeAnalysisResponse
from app.schemas.resume_schema import ResumeResponse, ResumeUploadResponse
from app.services.llm_service import (
    GeminiLLMService,
    LLMConfigurationError,
    LLMServiceError,
    get_llm_service,
)
from app.services.resume_analysis_service import analyze_resume
from app.services.resume_service import get_resume, save_resume
from app.utils.file_validator import validate_resume_file

router = APIRouter(prefix=f"{settings.api_v1_prefix}/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ResumeUploadResponse:
    extension = validate_resume_file(file)
    content = await file.read(settings.max_upload_size_bytes + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="Resume file is too large.")

    try:
        return save_resume(db, file, content, extension)
    except SQLAlchemyError as error:
        raise HTTPException(status_code=503, detail="Database unavailable.") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/{resume_id}", response_model=ResumeResponse)
def retrieve_resume(resume_id: int, db: Session = Depends(get_db)) -> ResumeResponse:
    resume = get_resume(db, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return resume


@router.post("/{resume_id}/analyze", response_model=ResumeAnalysisResponse)
def analyze_uploaded_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    llm_service: GeminiLLMService = Depends(get_llm_service),
) -> ResumeAnalysisResponse:
    try:
        analysis = analyze_resume(db, resume_id, llm_service)
        return ResumeAnalysisResponse(
            id=analysis.id,
            resume_id=analysis.resume_id,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
            **analysis.analysis,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except LLMConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except LLMServiceError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database unavailable.") from error
