from datetime import datetime

from pydantic import BaseModel, Field


class JobMatchData(BaseModel):
    overall_match_score: float = Field(ge=0, le=100)
    score_explanation: str = ""
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    partially_matching_skills: list[str] = Field(default_factory=list)
    experience_alignment: str = ""
    education_alignment: str = ""
    strengths_for_this_job: list[str] = Field(default_factory=list)
    skill_improvement_recommendations: list[str] = Field(default_factory=list)
    personalized_preparation_recommendations: list[str] = Field(default_factory=list)


class JobMatchResponse(JobMatchData):
    id: int
    job_id: int
    resume_id: int
    created_at: datetime
    updated_at: datetime
