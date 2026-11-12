from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SkillPerformance(BaseModel):
    technical_knowledge: float = Field(ge=0, le=100)
    problem_solving: float = Field(ge=0, le=100)
    communication: float = Field(ge=0, le=100)
    clarity: float = Field(ge=0, le=100)
    completeness: float = Field(ge=0, le=100)


class QuestionFeedback(BaseModel):
    sequence: int
    question: str
    question_type: str
    answer: str | None = None
    evaluation_score: float | None = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)
    suggested_improved_answer: str = ""
    feedback: str = ""


class FinalAssessment(BaseModel):
    overall_strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    areas_requiring_practice: list[str] = Field(default_factory=list)
    readiness_assessment: str
    summary: str = ""


class InterviewReportResponse(BaseModel):
    id: int
    interview_id: int
    resume_id: int
    job_id: int | None
    interview_type: str
    difficulty: str
    created_at: datetime
    overall_score: float = Field(ge=0, le=100)
    total_questions: int = Field(ge=0)
    answered_questions: int = Field(ge=0)
    completion_status: str
    duration_minutes: int = Field(ge=0)
    skill_performance: SkillPerformance
    question_feedback: list[QuestionFeedback]
    improvement_recommendations: list[str]
    missing_technical_concepts: list[str]
    recommended_preparation_topics: list[str]
    personalized_next_steps: list[str]
    final_assessment: FinalAssessment
    disclaimer: str


class ReportListItem(BaseModel):
    id: int
    interview_id: int
    resume_id: int
    job_id: int | None
    overall_score: float
    interview_type: str
    difficulty: str
    created_at: datetime
    total_questions: int
    answered_questions: int


class ReportListResponse(BaseModel):
    items: list[ReportListItem]
    page: int
    page_size: int
    total: int


class DashboardSummaryResponse(BaseModel):
    total_interviews_completed: int
    average_interview_score: float | None
    recent_interviews: list[ReportListItem]
    performance_trend: list[dict[str, Any]]
    skill_performance: SkillPerformance | None
    areas_for_improvement: list[str]
    matching_overview: dict[str, Any]
