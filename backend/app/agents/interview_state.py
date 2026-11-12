from typing import Any, TypedDict


class InterviewState(TypedDict, total=False):
    session_id: int
    resume_id: int
    job_id: int | None
    interview_type: str
    difficulty: str
    question_count: int
    duration_minutes: int
    resume_context: str
    job_context: str
    rag_context: list[dict[str, Any]]
    plan: dict[str, Any]
    current_question: str
    current_question_type: str
    current_answer: str
    evaluation: dict[str, Any]
    completed_questions: int
    status: str
    summary: dict[str, Any]
