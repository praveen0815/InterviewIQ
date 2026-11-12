from io import BytesIO

import fitz
from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_service import LLMServiceError, get_llm_service


class FakeLLM:
    def __init__(self) -> None:
        self.calls = 0

    def generate_json(self, prompt: str) -> dict:
        self.calls += 1
        if "RESUME:" in prompt:
            return {
                "professional_summary": "Python developer",
                "technical_skills": ["Python", "FastAPI"],
                "programming_languages": ["Python"],
                "frameworks_and_libraries": ["FastAPI"],
                "database_knowledge": ["PostgreSQL"],
                "ai_ml_knowledge": [],
                "tools_and_technologies": ["Docker"],
                "education_details": [],
                "work_experience": ["Built APIs"],
                "internship_experience": [],
                "projects": ["InterviewIQ"],
                "certifications": [],
                "strengths": ["API development"],
                "missing_or_unclear_information": [],
                "areas_for_improvement": ["Add measurable outcomes"],
            }
        if "JOB DESCRIPTION:" in prompt:
            return {
                "job_title": "Backend Engineer",
                "company_name": "",
                "summary": "Build Python APIs",
                "required_technical_skills": ["Python", "FastAPI"],
                "preferred_skills": ["Docker"],
                "required_experience": ["API development"],
                "education_requirements": [],
                "responsibilities": ["Build APIs"],
                "required_tools_and_technologies": ["PostgreSQL"],
                "key_qualifications": ["Python experience"],
            }
        return {
            "overall_match_score": 82,
            "score_explanation": "Required skills align strongly.",
            "matching_skills": ["Python", "FastAPI"],
            "missing_skills": [],
            "partially_matching_skills": [],
            "experience_alignment": "Aligned with API development.",
            "education_alignment": "No education requirement was provided.",
            "strengths_for_this_job": ["API development"],
            "skill_improvement_recommendations": ["Deepen PostgreSQL skills"],
            "personalized_preparation_recommendations": ["Prepare API design examples"],
        }


def make_pdf() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Python developer with FastAPI experience")
    content = document.tobytes()
    document.close()
    return content


def test_phase3_persists_analysis_and_match(client, monkeypatch) -> None:
    fake_llm = FakeLLM()
    app.dependency_overrides[get_llm_service] = lambda: fake_llm
    try:
        resume_response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", make_pdf(), "application/pdf")},
        )
        resume_id = resume_response.json()["id"]

        analysis = client.post(f"/api/v1/resumes/{resume_id}/analyze")
        assert analysis.status_code == 200
        assert analysis.json()["technical_skills"] == ["Python", "FastAPI"]
        assert client.post(f"/api/v1/resumes/{resume_id}/analyze").status_code == 200

        job = client.post(
            "/api/v1/jobs/analyze",
            json={"description": "Backend Engineer needed. Python and FastAPI experience required."},
        )
        assert job.status_code == 201
        job_id = job.json()["id"]

        match = client.post(f"/api/v1/jobs/{job_id}/match/{resume_id}")
        assert match.status_code == 200
        assert match.json()["overall_match_score"] == 82
        assert fake_llm.calls == 3
    finally:
        app.dependency_overrides.pop(get_llm_service, None)


def test_phase3_missing_ids_and_validation(client) -> None:
    assert client.post("/api/v1/resumes/999999/analyze").status_code == 404
    assert client.post("/api/v1/jobs/999999/match/999999").status_code == 404
    assert client.post("/api/v1/jobs/analyze", json={"description": "too short"}).status_code == 422


def test_llm_failure_is_reported_as_bad_gateway(client, monkeypatch) -> None:
    class BrokenLLM:
        def generate_json(self, prompt: str) -> dict:
            raise LLMServiceError("Gemini request failed.")

    app.dependency_overrides[get_llm_service] = BrokenLLM
    try:
        response = client.post(
            "/api/v1/jobs/analyze",
            json={"description": "A sufficiently detailed backend engineering job description."},
        )
        assert response.status_code == 502
    finally:
        app.dependency_overrides.pop(get_llm_service, None)
