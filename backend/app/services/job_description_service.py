from sqlalchemy.orm import Session

from app.models.job_description import JobDescription
from app.schemas.job_description_schema import JobDescriptionAnalysis
from app.services.llm_service import GeminiLLMService


def analyze_job_description(
    db: Session, description: str, llm_service: GeminiLLMService
) -> JobDescription:
    prompt = f"""Analyze this job description using only information explicitly provided.
Do not assume a company, seniority, years of experience, education, or skill is
present when it is not. Use empty strings or arrays when unavailable. Return JSON
with these keys: job_title, company_name, summary, required_technical_skills,
preferred_skills, required_experience, education_requirements, responsibilities,
required_tools_and_technologies, key_qualifications. Arrays must contain concise
strings.

JOB DESCRIPTION:
{description}
"""
    data = JobDescriptionAnalysis.model_validate(llm_service.generate_json(prompt))
    job = JobDescription(description=description, analysis=data.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
