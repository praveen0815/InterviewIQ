from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.connection import get_db
from app.rag.rag_service import RAGService, RAGServiceError
from app.schemas.rag_schema import RAGIndexResponse, RAGQueryRequest, RAGQueryResponse
from app.services.llm_service import (
    GeminiLLMService,
    LLMConfigurationError,
    LLMServiceError,
    get_llm_service,
)

router = APIRouter(prefix=f"{settings.api_v1_prefix}/rag", tags=["rag"])


def get_rag_service() -> RAGService:
    return RAGService()


def _index(
    result: dict,
) -> RAGIndexResponse:
    return RAGIndexResponse(**result)


@router.post("/index/resume/{resume_id}", response_model=RAGIndexResponse)
def index_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
) -> RAGIndexResponse:
    try:
        return _index(rag_service.index_resume(db, resume_id))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RAGServiceError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/index/job/{job_id}", response_model=RAGIndexResponse)
def index_job(
    job_id: int,
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
) -> RAGIndexResponse:
    try:
        return _index(rag_service.index_job(db, job_id))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RAGServiceError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/reindex/resume/{resume_id}", response_model=RAGIndexResponse)
def reindex_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
) -> RAGIndexResponse:
    try:
        return _index(rag_service.index_resume(db, resume_id, force=True))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RAGServiceError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/query", response_model=RAGQueryResponse)
def query_rag(
    payload: RAGQueryRequest,
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
    llm_service: GeminiLLMService = Depends(get_llm_service),
) -> RAGQueryResponse:
    try:
        return RAGQueryResponse(
            **rag_service.query(db, payload.resume_id, payload.question, llm_service, payload.job_id)
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except LLMConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except LLMServiceError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except RAGServiceError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
