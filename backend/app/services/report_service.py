from collections.abc import Iterable
from statistics import mean
from typing import Any

import fitz
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.interview import AnswerEvaluation, CandidateAnswer, InterviewQuestion, InterviewSession
from app.models.job_match import JobMatch
from app.models.report import InterviewReport
from app.schemas.report_schema import (
    DashboardSummaryResponse,
    InterviewReportResponse,
    ReportListItem,
    ReportListResponse,
    SkillPerformance,
)


DISCLAIMER = (
    "This is an AI-generated preparation assessment based on the recorded interview. "
    "It is not a guaranteed hiring prediction or employment decision."
)


class ReportServiceError(RuntimeError):
    pass


def _unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _average(values: Iterable[float]) -> float:
    values = list(values)
    return round(mean(values), 2) if values else 0.0


class ReportService:
    def _evaluation_rows(self, db: Session, session_id: int):
        return (
            db.query(InterviewQuestion, CandidateAnswer, AnswerEvaluation)
            .outerjoin(CandidateAnswer, CandidateAnswer.question_id == InterviewQuestion.id)
            .outerjoin(AnswerEvaluation, AnswerEvaluation.answer_id == CandidateAnswer.id)
            .filter(InterviewQuestion.session_id == session_id)
            .order_by(InterviewQuestion.sequence)
            .all()
        )

    def _build_data(self, db: Session, session: InterviewSession) -> dict[str, Any]:
        rows = self._evaluation_rows(db, session.id)
        evaluations = [evaluation for _, _, evaluation in rows if evaluation is not None]
        if session.status != "completed":
            raise ValueError("An interview report is available only after the interview is completed.")
        if not evaluations:
            raise ValueError("An interview report requires at least one evaluated answer.")

        question_feedback = []
        missing_concepts: list[str] = []
        weaknesses: list[str] = []
        for question, answer, evaluation in rows:
            question_feedback.append(
                {
                    "sequence": question.sequence + 1,
                    "question": question.question,
                    "question_type": question.question_type,
                    "answer": answer.answer if answer else None,
                    "evaluation_score": round(evaluation.score, 2) if evaluation else None,
                    "strengths": list(evaluation.strengths or []) if evaluation else [],
                    "weaknesses": list(evaluation.weaknesses or []) if evaluation else [],
                    "missing_concepts": list(evaluation.missing_concepts or []) if evaluation else [],
                    "suggested_improved_answer": evaluation.suggested_improved_answer if evaluation else "",
                    "feedback": evaluation.feedback if evaluation else "",
                }
            )
            if evaluation:
                missing_concepts.extend(evaluation.missing_concepts or [])
                weaknesses.extend(evaluation.weaknesses or [])

        skill_performance = {
            "technical_knowledge": _average(item.technical_correctness for item in evaluations),
            "problem_solving": _average(item.problem_solving for item in evaluations),
            "communication": _average(item.communication for item in evaluations),
            "clarity": _average(item.clarity for item in evaluations),
            "completeness": _average(item.completeness for item in evaluations),
        }
        summary = session.summary or {}
        strengths = _unique(
            value for item in evaluations for value in (item.strengths or [])
        )
        improvement_areas = _unique(
            [*weaknesses, *missing_concepts, *summary.get("improvement_areas", [])]
        )
        score = _average(item.score for item in evaluations)
        if score >= 80:
            readiness = "Strong preparation baseline; continue practicing under time pressure."
        elif score >= 60:
            readiness = "Developing preparation baseline; targeted practice is recommended."
        else:
            readiness = "Early preparation baseline; focus on the listed fundamentals before repeating the interview."

        return {
            "interview_type": session.interview_type,
            "difficulty": session.difficulty,
            "overall_score": score,
            "total_questions": len(rows),
            "answered_questions": len(evaluations),
            "completion_status": session.status,
            "duration_minutes": session.duration_minutes,
            "skill_performance": skill_performance,
            "question_feedback": question_feedback,
            "improvement_recommendations": improvement_areas,
            "missing_technical_concepts": _unique(missing_concepts),
            "recommended_preparation_topics": _unique(missing_concepts + improvement_areas),
            "personalized_next_steps": [
                f"Practice {topic} with one timed answer." for topic in improvement_areas[:5]
            ],
            "final_assessment": {
                "overall_strengths": strengths,
                "weaknesses": _unique(weaknesses),
                "areas_requiring_practice": improvement_areas,
                "readiness_assessment": readiness,
                "summary": str(summary.get("summary", "")),
            },
            "disclaimer": DISCLAIMER,
        }

    def generate(self, db: Session, interview_id: int) -> InterviewReport:
        session = db.get(InterviewSession, interview_id)
        if session is None:
            raise LookupError("Interview not found.")
        data = self._build_data(db, session)
        report = db.query(InterviewReport).filter_by(interview_id=interview_id).one_or_none()
        if report is None:
            report = InterviewReport(
                interview_id=session.id,
                resume_id=session.resume_id,
                job_id=session.job_id,
                overall_score=data["overall_score"],
                report_data=data,
            )
            db.add(report)
        else:
            report.overall_score = data["overall_score"]
            report.report_data = data
            report.resume_id = session.resume_id
            report.job_id = session.job_id
        db.commit()
        db.refresh(report)
        return report

    def get(self, db: Session, report_id: int) -> InterviewReport:
        report = db.get(InterviewReport, report_id)
        if report is None:
            raise LookupError("Report not found.")
        return report

    def get_for_interview(self, db: Session, interview_id: int) -> InterviewReport:
        report = db.query(InterviewReport).filter_by(interview_id=interview_id).one_or_none()
        if report is not None:
            return report
        return self.generate(db, interview_id)

    @staticmethod
    def response(report: InterviewReport) -> InterviewReportResponse:
        return InterviewReportResponse(
            id=report.id,
            interview_id=report.interview_id,
            resume_id=report.resume_id,
            job_id=report.job_id,
            created_at=report.created_at,
            **report.report_data,
        )

    def list_reports(
        self, db: Session, page: int, page_size: int, resume_id: int | None = None
    ) -> ReportListResponse:
        query = db.query(InterviewReport)
        if resume_id is not None:
            query = query.filter(InterviewReport.resume_id == resume_id)
        total = query.count()
        reports = query.order_by(InterviewReport.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        items = [
            ReportListItem(
                id=report.id,
                interview_id=report.interview_id,
                resume_id=report.resume_id,
                job_id=report.job_id,
                overall_score=report.overall_score,
                interview_type=report.report_data["interview_type"],
                difficulty=report.report_data["difficulty"],
                created_at=report.created_at,
                total_questions=report.report_data["total_questions"],
                answered_questions=report.report_data["answered_questions"],
            )
            for report in reports
        ]
        return ReportListResponse(items=items, page=page, page_size=page_size, total=total)

    def dashboard(self, db: Session, page_size: int = 5) -> DashboardSummaryResponse:
        reports = db.query(InterviewReport).order_by(InterviewReport.created_at.asc()).all()
        recent = list(reversed(reports[-page_size:]))
        skill_values = {
            key: [report.report_data["skill_performance"][key] for report in reports]
            for key in SkillPerformance.model_fields
        }
        improvement_areas = _unique(
            area
            for report in reports
            for area in report.report_data.get("improvement_recommendations", [])
        )
        matching = db.query(
            func.count(JobMatch.id), func.avg(JobMatch.match_score)
        ).one()
        return DashboardSummaryResponse(
            total_interviews_completed=len(reports),
            average_interview_score=_average(report.overall_score for report in reports) if reports else None,
            recent_interviews=[
                ReportListItem(
                    id=report.id,
                    interview_id=report.interview_id,
                    resume_id=report.resume_id,
                    job_id=report.job_id,
                    overall_score=report.overall_score,
                    interview_type=report.report_data["interview_type"],
                    difficulty=report.report_data["difficulty"],
                    created_at=report.created_at,
                    total_questions=report.report_data["total_questions"],
                    answered_questions=report.report_data["answered_questions"],
                )
                for report in recent
            ],
            performance_trend=[
                {"date": report.created_at.isoformat(), "score": report.overall_score}
                for report in reports
            ],
            skill_performance=SkillPerformance(**{
                key: _average(values) for key, values in skill_values.items()
            }) if reports else None,
            areas_for_improvement=improvement_areas,
            matching_overview={
                "total_matches": int(matching[0] or 0),
                "average_match_score": round(float(matching[1]), 2) if matching[1] is not None else None,
            },
        )

    @staticmethod
    def pdf(report: InterviewReport) -> bytes:
        data = report.report_data
        document = fitz.open()
        page = document.new_page()
        lines = [
            "InterviewIQ Interview Report",
            data["disclaimer"],
            "",
            f"Interview {report.interview_id} | {data['interview_type']} | {data['difficulty']}",
            f"Overall score: {data['overall_score']}/100",
            f"Questions answered: {data['answered_questions']}/{data['total_questions']}",
            f"Configured duration: {data['duration_minutes']} minutes",
            "",
            "Skill performance",
        ]
        lines.extend(f"- {key.replace('_', ' ').title()}: {value}/100" for key, value in data["skill_performance"].items())
        lines.extend(["", "Question feedback"])
        for item in data["question_feedback"]:
            lines.extend([
                f"{item['sequence']}. {item['question']}",
                f"Score: {item['evaluation_score'] if item['evaluation_score'] is not None else 'Not answered'}/100",
                f"Answer: {item['answer'] or 'Not answered'}",
                f"Feedback: {item['feedback']}",
                f"Improved answer: {item['suggested_improved_answer']}",
                "",
            ])
        lines.extend(["Improvement recommendations", *[f"- {item}" for item in data["improvement_recommendations"]]])
        y = 48
        for line in lines:
            if y > 770:
                page = document.new_page()
                y = 48
            page.insert_text((48, y), line[:180], fontsize=9)
            y += 14
        return document.tobytes()
