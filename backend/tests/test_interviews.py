import fitz

from app.agents.interview_graph import build_interview_graph
from app.main import app
from app.routers.interview_router import get_interview_service
from app.routers.rag_router import get_rag_service
from app.services.llm_service import get_llm_service


class FakeLLM:
    def generate_json(self, prompt):
        if "RESUME:" in prompt:
            return {
                "professional_summary": "Python developer",
                "technical_skills": ["Python", "FastAPI"],
                "programming_languages": ["Python"],
                "frameworks_and_libraries": ["FastAPI"],
                "database_knowledge": [],
                "ai_ml_knowledge": [],
                "tools_and_technologies": [],
                "education_details": [],
                "work_experience": ["Built APIs"],
                "internship_experience": [],
                "projects": [],
                "certifications": [],
                "strengths": ["API development"],
                "missing_or_unclear_information": [],
                "areas_for_improvement": [],
            }
        if "Generate the next single" in prompt:
            return {"question": "How did you build the API?", "question_type": "Technical"}
        if "interview plan" in prompt:
            return {"focus_areas": ["APIs"], "question_types": ["Technical"], "rationale": "Evidence"}
        if "Evaluate" in prompt:
            return {
                "technical_correctness": 80, "relevance": 90, "completeness": 70,
                "clarity": 80, "problem_solving": 70, "communication": 90,
                "strengths": ["Clear explanation"], "weaknesses": ["More detail needed"],
                "missing_concepts": [], "suggested_improved_answer": "Add tradeoffs.",
                "feedback": "Good answer.",
            }
        if "Summarize" in prompt:
            return {"overall_score": 0, "strengths": ["Clarity"], "improvement_areas": ["Detail"], "summary": "Solid"}
        return {"question": "How did you build the API?", "question_type": "Technical"}


class FakeRetriever:
    def retrieve(self, *args, **kwargs):
        return [{"text": "Built FastAPI services.", "metadata": {"source_type": "resume"}}]


def make_pdf() -> bytes:
    document = fitz.open()
    document.new_page().insert_text((72, 72), "Python developer with FastAPI experience")
    content = document.tobytes()
    document.close()
    return content


def prepare_candidate(client, monkeypatch):
    app.dependency_overrides[get_llm_service] = lambda: FakeLLM()
    upload = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.pdf", make_pdf(), "application/pdf")},
    )
    resume_id = upload.json()["id"]
    analysis = client.post(f"/api/v1/resumes/{resume_id}/analyze")
    assert analysis.status_code == 200
    app.dependency_overrides[get_interview_service] = lambda: __import__(
        "app.services.interview_service", fromlist=["InterviewService"]
    ).InterviewService(FakeRetriever())
    return resume_id


def test_interview_graph_runs_with_mocked_llm():
    state = build_interview_graph(FakeLLM()).invoke({
        "interview_type": "Technical", "difficulty": "Beginner", "question_count": 1,
        "resume_context": "FastAPI", "job_context": "", "rag_context": [],
    })
    assert state["current_question"] == "How did you build the API?"


def test_interview_lifecycle_and_duplicate_answer(client, monkeypatch):
    resume_id = prepare_candidate(client, monkeypatch)
    try:
        started = client.post("/api/v1/interviews/start", json={
            "resume_id": resume_id, "interview_type": "Technical",
            "difficulty": "Beginner", "question_count": 1, "duration_minutes": 10,
        })
        assert started.status_code == 201
        interview_id = started.json()["id"]
        assert client.get(f"/api/v1/interviews/{interview_id}").status_code == 200
        answered = client.post(
            f"/api/v1/interviews/{interview_id}/answer",
            json={"answer": "I built it with FastAPI."},
        )
        assert answered.status_code == 200
        duplicate = client.post(
            f"/api/v1/interviews/{interview_id}/answer",
            json={"answer": "Duplicate"},
        )
        assert duplicate.status_code == 409
        completed = client.post(f"/api/v1/interviews/{interview_id}/complete")
        assert completed.status_code == 200
        assert completed.json()["status"] == "completed"
    finally:
        app.dependency_overrides.pop(get_llm_service, None)
        app.dependency_overrides.pop(get_interview_service, None)


def test_invalid_interview_id(client):
    assert client.get("/api/v1/interviews/999999").status_code == 404
