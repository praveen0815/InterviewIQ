from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResumeAnalysisData(BaseModel):
    professional_summary: str = ""
    technical_skills: list[str] = Field(default_factory=list)
    programming_languages: list[str] = Field(default_factory=list)
    frameworks_and_libraries: list[str] = Field(default_factory=list)
    database_knowledge: list[str] = Field(default_factory=list)
    ai_ml_knowledge: list[str] = Field(default_factory=list)
    tools_and_technologies: list[str] = Field(default_factory=list)
    education_details: list[str] = Field(default_factory=list)
    work_experience: list[str] = Field(default_factory=list)
    internship_experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    missing_or_unclear_information: list[str] = Field(default_factory=list)
    areas_for_improvement: list[str] = Field(default_factory=list)


class ResumeAnalysisResponse(ResumeAnalysisData):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int
    created_at: datetime
    updated_at: datetime
