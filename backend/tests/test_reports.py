from app.models.interview import AnswerEvaluation, CandidateAnswer, InterviewQuestion, InterviewSession
from app.models.resume import Resume
from app.services.report_service import ReportService


def make_completed_interview(db_session):
    resume = Resume(
        original_filename="report-resume.pdf",
        file_type="pdf",
        file_path="uploads/report-resume.pdf",
        extracted_text="Python engineer",
    )
    db_session.add(resume)
    db_session.flush()
    session = InterviewSession(
        resume_id=resume.id,
        interview_type="Technical",
        difficulty="Intermediate",
        question_count=2,
        duration_minutes=30,
        status="completed",
        current_question_index=2,
        state={},
        summary={
            "summary": "Good preparation baseline.",
            "strengths": ["Clear explanation"],
            "improvement_areas": ["Testing"],
        },
    )
    db_session.add(session)
    db_session.flush()
    for sequence, score in enumerate((80, 60)):
        question = InterviewQuestion(
            session_id=session.id,
            sequence=sequence,
            question=f"Question {sequence + 1}",
            question_type="Technical",
            status="answered",
        )
        db_session.add(question)
        db_session.flush()
        answer = CandidateAnswer(question_id=question.id, answer=f"Answer {sequence + 1}")
        db_session.add(answer)
        db_session.flush()
        db_session.add(AnswerEvaluation(
            answer_id=answer.id,
            score=score,
            technical_correctness=score,
            relevance=score,
            completeness=score,
            clarity=score,
            problem_solving=score,
            communication=score,
            strengths=["Clear explanation"],
            weaknesses=["Testing"],
            missing_concepts=["Test isolation"],
            suggested_improved_answer="Include a test strategy.",
            feedback="Keep the answer structured.",
        ))
    db_session.commit()
    return session.id


def test_report_generation_persists_actual_scores_and_pdf(client, db_session):
    interview_id = make_completed_interview(db_session)

    response = client.get(f"/api/v1/interviews/{interview_id}/report")
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_score"] == 70
    assert payload["answered_questions"] == 2
    assert payload["skill_performance"]["technical_knowledge"] == 70
    assert payload["question_feedback"][0]["answer"] == "Answer 1"
    assert payload["disclaimer"].startswith("This is an AI-generated")

    report_id = payload["id"]
    listed = client.get("/api/v1/reports?page=1&page_size=1")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == report_id

    pdf = client.get(f"/api/v1/reports/{report_id}/pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")


def test_dashboard_and_missing_or_incomplete_reports(client, db_session):
    empty = client.get("/api/v1/dashboard/summary")
    assert empty.status_code == 200
    assert empty.json()["total_interviews_completed"] == 0
    assert empty.json()["average_interview_score"] is None
    assert empty.json()["skill_performance"] is None

    assert client.get("/api/v1/reports/999999").status_code == 404
    assert client.get("/api/v1/interviews/999999/report").status_code == 404

    resume = Resume(
        original_filename="incomplete.pdf",
        file_type="pdf",
        file_path="uploads/incomplete.pdf",
        extracted_text="Candidate",
    )
    db_session.add(resume)
    db_session.flush()
    session = InterviewSession(
        resume_id=resume.id,
        interview_type="HR",
        difficulty="Beginner",
        question_count=1,
        duration_minutes=10,
        status="active",
        current_question_index=0,
        state={},
    )
    db_session.add(session)
    db_session.commit()

    response = client.get(f"/api/v1/interviews/{session.id}/report")
    assert response.status_code == 409
    assert "only after" in response.json()["detail"]


def test_report_service_does_not_invent_unanswered_scores(db_session):
    interview_id = make_completed_interview(db_session)
    report = ReportService().get_for_interview(db_session, interview_id)
    assert all(item["evaluation_score"] is not None for item in report.report_data["question_feedback"])
