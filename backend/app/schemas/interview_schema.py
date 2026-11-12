from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InterviewType(StrEnum):
    technical = "Technical"
    hr = "HR"
    behavioral = "Behavioral"
    mixed = "Mixed"


class InterviewDifficulty(StrEnum):
    beginner = "Beginner"
    intermediate = "Intermediate"
    advanced = "Advanced"


class InterviewStartRequest(BaseModel):
    resume_id: int = Field(gt=0)
    job_id: int | None = Field(default=None, gt=0)
    interview_type: InterviewType
    difficulty: InterviewDifficulty
    question_count: int = Field(ge=1, le=20)
    duration_minutes: int = Field(ge=5, le=180)


class InterviewAnswerRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=20_000)


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    score: float
    technical_correctness: float
    relevance: float
    completeness: float
    clarity: float
    problem_solving: float
    communication: float
    strengths: list[str]
    weaknesses: list[str]
    missing_concepts: list[str]
    suggested_improved_answer: str
    feedback: str


class QuestionResponse(BaseModel):
    id: int
    sequence: int
    question: str
    question_type: str
    status: str
    answer: str | None = None
    evaluation: EvaluationResponse | None = None


class InterviewResponse(BaseModel):
    id: int
    resume_id: int
    job_id: int | None
    interview_type: str
    difficulty: str
    question_count: int
    duration_minutes: int
    status: str
    current_question_index: int
    question: QuestionResponse | None = None
    questions: list[QuestionResponse] = Field(default_factory=list)
    summary: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
