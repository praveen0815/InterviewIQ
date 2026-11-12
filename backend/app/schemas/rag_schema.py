from typing import Any

from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    resume_id: int = Field(gt=0)
    job_id: int | None = Field(default=None, gt=0)
    question: str = Field(min_length=1, max_length=2_000)


class RAGContext(BaseModel):
    text: str
    metadata: dict[str, Any]
    distance: float | None = None


class RAGQueryResponse(BaseModel):
    answer: str
    retrieved_context: list[RAGContext]
    source_documents: list[dict[str, Any]]


class RAGIndexResponse(BaseModel):
    source_type: str
    source_id: int
    chunks_indexed: int
    content_hash: str | None = None
    duplicate: bool = False
    reindexed: bool = False
