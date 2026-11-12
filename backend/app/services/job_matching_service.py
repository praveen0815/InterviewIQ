from sqlalchemy.orm import Session

from app.models.job_description import JobDescription
from app.models.job_match import JobMatch
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.schemas.job_description_schema import JobDescriptionAnalysis
from app.schemas.job_matching_schema import JobMatchData
from app.schemas.resume_analysis_schema import ResumeAnalysisData
from app.services.llm_service import GeminiLLMService


def match_resume_to_job(
    db: Session, job_id: int, resume_id: int, llm_service: GeminiLLMService
) -> JobMatch:
    job = db.get(JobDescription, job_id)
    resume = db.get(Resume, resume_id)
    resume_analysis = (
        db.query(ResumeAnalysis).filter_by(resume_id=resume_id).one_or_none()
        if resume is not None
        else None
    )
    if job is None:
        raise LookupError("Job description not found.")
    if resume is None:
        raise LookupError("Resume not found.")
    if resume_analysis is None:
        raise ValueError("Analyze the resume before matching it to a job.")

    existing = (
        db.query(JobMatch).filter_by(job_id=job_id, resume_id=resume_id).one_or_none()
    )
    if existing is not None:
        return existing

    job_data = JobDescriptionAnalysis.model_validate(job.analysis)
    resume_data = ResumeAnalysisData.model_validate(resume_analysis.analysis)
    prompt = f"""Compare this resume analysis to this job analysis using only the
provided evidence. Distinguish required from preferred skills. Calculate a
defensible 0-100 match score based on required skills (50%), experience (25%),
education (10%), and preferred skills (15%); explain the calculation and never
describe it as a hiring probability. Return JSON with keys:
overall_match_score, score_explanation, matching_skills, missing_skills,
partially_matching_skills, experience_alignment, education_alignment,
strengths_for_this_job, skill_improvement_recommendations,
personalized_preparation_recommendations.

RESUME ANALYSIS:
{resume_data.model_dump_json()}

JOB ANALYSIS:
{job_data.model_dump_json()}
"""
    data = JobMatchData.model_validate(llm_service.generate_json(prompt))
    match = JobMatch(
        job_id=job_id,
        resume_id=resume_id,
        match_score=data.overall_match_score,
        result=data.model_dump(),
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match
