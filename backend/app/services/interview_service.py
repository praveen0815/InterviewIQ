import json
from typing import Any

from sqlalchemy.orm import Session

from app.agents.interview_graph import build_answer_graph, build_interview_graph
from app.agents.interview_state import InterviewState
from app.config.settings import settings
from app.models.interview import AnswerEvaluation, CandidateAnswer, InterviewQuestion, InterviewSession
from app.models.job_description import JobDescription
from app.models.job_match import JobMatch
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStoreError
from app.services.llm_service import GeminiLLMService
from app.services.report_service import ReportService
from app.schemas.interview_schema import InterviewStartRequest


class InterviewServiceError(RuntimeError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True)


class InterviewService:
    def __init__(self, retriever: Retriever | None = None) -> None:
        self.retriever = retriever or Retriever()

    def _load_state(self, db: Session, request: InterviewStartRequest) -> InterviewState:
        resume = db.get(Resume, request.resume_id)
        analysis = db.query(ResumeAnalysis).filter_by(resume_id=request.resume_id).one_or_none()
        if resume is None:
            raise LookupError("Resume not found.")
        if analysis is None:
            raise ValueError("Analyze the resume before starting an interview.")
        job = db.get(JobDescription, request.job_id) if request.job_id else None
        if request.job_id and job is None:
            raise LookupError("Job description not found.")
        if job is not None and db.query(JobMatch).filter_by(
            job_id=job.id, resume_id=resume.id
        ).one_or_none() is None:
            raise ValueError("Match the resume to the job before starting an interview.")
        rag_context: list[dict[str, Any]] = []
        try:
            rag_context = self.retriever.retrieve(
                "interview preparation and relevant candidate experience",
                request.resume_id,
                request.job_id,
                settings.rag_top_k,
            )
        except (VectorStoreError, RuntimeError) as error:
            raise InterviewServiceError(f"Unable to retrieve interview context: {error}") from error
        return {
            "resume_id": request.resume_id,
            "job_id": request.job_id,
            "interview_type": request.interview_type.value,
            "difficulty": request.difficulty.value,
            "question_count": request.question_count,
            "duration_minutes": request.duration_minutes,
            "resume_context": _json(analysis.analysis),
            "job_context": _json(job.analysis) if job else "",
            "rag_context": rag_context,
            "completed_questions": 0,
            "status": "active",
        }

    def start(self, db: Session, request: InterviewStartRequest, llm_service: GeminiLLMService) -> InterviewSession:
        state = self._load_state(db, request)
        try:
            state = build_interview_graph(llm_service).invoke(state)
        except Exception as error:
            db.rollback()
            raise InterviewServiceError("Unable to create the interview plan or first question.") from error
        session = InterviewSession(
            resume_id=request.resume_id,
            job_id=request.job_id,
            interview_type=request.interview_type.value,
            difficulty=request.difficulty.value,
            question_count=request.question_count,
            duration_minutes=request.duration_minutes,
            state=dict(state),
            status="active",
        )
        db.add(session)
        db.flush()
        db.add(InterviewQuestion(
            session_id=session.id,
            sequence=0,
            question=state["current_question"],
            question_type=state["current_question_type"],
            status="pending",
        ))
        db.commit()
        db.refresh(session)
        return session

    def _question(self, db: Session, session: InterviewSession, sequence: int | None = None):
        sequence = session.current_question_index if sequence is None else sequence
        question = db.query(InterviewQuestion).filter_by(
            session_id=session.id, sequence=sequence
        ).one_or_none()
        if question is None:
            raise LookupError("Interview question not found.")
        return question

    def answer(
        self, db: Session, session_id: int, answer_text: str, llm_service: GeminiLLMService
    ) -> tuple[InterviewSession, InterviewQuestion, AnswerEvaluation]:
        session = db.get(InterviewSession, session_id)
        if session is None:
            raise LookupError("Interview not found.")
        if session.status != "active":
            raise ValueError("Interview is not active.")
        question = self._question(db, session)
        if db.query(CandidateAnswer).filter_by(question_id=question.id).one_or_none() is not None:
            raise ValueError("This question has already been answered.")
        state: InterviewState = dict(session.state)
        state["current_question"] = question.question
        state["current_answer"] = answer_text
        try:
            result = build_answer_graph(llm_service).invoke(state)
        except Exception as error:
            db.rollback()
            raise InterviewServiceError("Unable to evaluate the answer.") from error
        evaluation_data = result["evaluation"]
        candidate_answer = CandidateAnswer(question_id=question.id, answer=answer_text)
        db.add(candidate_answer)
        db.flush()
        evaluation = AnswerEvaluation(
            answer_id=candidate_answer.id,
            score=float(evaluation_data["score"]),
            **{key: float(evaluation_data.get(key, 0)) for key in (
                "technical_correctness", "relevance", "completeness", "clarity",
                "problem_solving", "communication",
            )},
            strengths=evaluation_data.get("strengths", []),
            weaknesses=evaluation_data.get("weaknesses", []),
            missing_concepts=evaluation_data.get("missing_concepts", []),
            suggested_improved_answer=evaluation_data.get("suggested_improved_answer", ""),
            feedback=evaluation_data.get("feedback", ""),
        )
        db.add(evaluation)
        question.status = "answered"
        session.current_question_index += 1
        completed = session.current_question_index
        state.update(result)
        state["completed_questions"] = completed
        if completed >= session.question_count:
            session.status = "ready_to_complete"
        else:
            next_question = InterviewQuestion(
                session_id=session.id,
                sequence=completed,
                question=result["current_question"],
                question_type=result["current_question_type"],
                status="pending",
            )
            db.add(next_question)
        session.state = dict(state)
        db.commit()
        db.refresh(session)
        db.refresh(evaluation)
        return session, question, evaluation

    def complete(self, db: Session, session_id: int, llm_service: GeminiLLMService) -> InterviewSession:
        session = db.get(InterviewSession, session_id)
        if session is None:
            raise LookupError("Interview not found.")
        evaluations = (
            db.query(AnswerEvaluation)
            .join(CandidateAnswer, CandidateAnswer.id == AnswerEvaluation.answer_id)
            .join(InterviewQuestion, InterviewQuestion.id == CandidateAnswer.question_id)
            .filter(InterviewQuestion.session_id == session.id)
            .all()
        )
        if not evaluations:
            raise ValueError("Answer at least one question before completing the interview.")
        payload = [{"score": item.score, "feedback": item.feedback} for item in evaluations]
        try:
            summary = llm_service.generate_json(
                f"""Summarize this completed interview as JSON with keys overall_score, strengths,
improvement_areas, summary. Use only these evaluations and do not invent facts: {_json(payload)}"""
            )
        except Exception as error:
            db.rollback()
            raise InterviewServiceError("Unable to generate the interview summary.") from error
        summary["overall_score"] = round(
            sum(item.score for item in evaluations) / len(evaluations), 2
        )
        session.status = "completed"
        session.summary = summary
        session.state = {**session.state, "status": "completed", "summary": summary}
        db.commit()
        db.refresh(session)
        ReportService().generate(db, session.id)
        return session
