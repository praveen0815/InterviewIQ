from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobDescriptionCreate(BaseModel):
    description: str = Field(min_length=20, max_length=50_000)


class JobDescriptionAnalysis(BaseModel):
    job_title: str = ""
    company_name: str = ""
    summary: str = ""
    required_technical_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    required_experience: list[str] = Field(default_factory=list)
    education_requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    required_tools_and_technologies: list[str] = Field(default_factory=list)
    key_qualifications: list[str] = Field(default_factory=list)


class JobDescriptionResponse(JobDescriptionAnalysis):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    created_at: datetime
    updated_at: datetime
