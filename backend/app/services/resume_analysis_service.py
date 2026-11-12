from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.schemas.resume_analysis_schema import ResumeAnalysisData
from app.services.llm_service import GeminiLLMService


def analyze_resume(
    db: Session, resume_id: int, llm_service: GeminiLLMService
) -> ResumeAnalysis:
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise LookupError("Resume not found.")

    existing = db.query(ResumeAnalysis).filter_by(resume_id=resume_id).one_or_none()
    if existing is not None:
        return existing

    prompt = f"""Analyze the resume below using only explicit evidence in the text.
Do not invent skills, experience, qualifications, dates, or education. Use an empty
string or empty list when information is unavailable. Return one JSON object with
these keys: professional_summary, technical_skills, programming_languages,
frameworks_and_libraries, database_knowledge, ai_ml_knowledge,
tools_and_technologies, education_details, work_experience, internship_experience,
projects, certifications, strengths, missing_or_unclear_information,
areas_for_improvement. All fields except professional_summary are arrays of concise
evidence-based strings.

RESUME:
{resume.extracted_text}
"""
    data = ResumeAnalysisData.model_validate(llm_service.generate_json(prompt))
    analysis = ResumeAnalysis(resume_id=resume_id, analysis=data.model_dump())
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis
