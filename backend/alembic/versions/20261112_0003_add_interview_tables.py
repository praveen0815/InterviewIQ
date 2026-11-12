"""add persistent interview tables

Revision ID: 20261112_0003
Revises: 20261106_0002
Create Date: 2026-11-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261112_0003"
down_revision: Union[str, None] = "20261106_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("interview_type", sa.String(length=20), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("current_question_index", sa.Integer(), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["job_descriptions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interview_sessions_resume_id", "interview_sessions", ["resume_id"])
    op.create_index("ix_interview_sessions_job_id", "interview_sessions", ["job_id"])
    op.create_table(
        "interview_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "sequence", name="uq_interview_question_sequence"),
    )
    op.create_index("ix_interview_questions_session_id", "interview_questions", ["session_id"])
    op.create_table(
        "candidate_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["interview_questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id"),
    )
    op.create_index("ix_candidate_answers_question_id", "candidate_answers", ["question_id"])
    op.create_table(
        "answer_evaluations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("answer_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("technical_correctness", sa.Float(), nullable=False),
        sa.Column("relevance", sa.Float(), nullable=False),
        sa.Column("completeness", sa.Float(), nullable=False),
        sa.Column("clarity", sa.Float(), nullable=False),
        sa.Column("problem_solving", sa.Float(), nullable=False),
        sa.Column("communication", sa.Float(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("missing_concepts", sa.JSON(), nullable=False),
        sa.Column("suggested_improved_answer", sa.Text(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["answer_id"], ["candidate_answers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("answer_id"),
    )
    op.create_index("ix_answer_evaluations_answer_id", "answer_evaluations", ["answer_id"])


def downgrade() -> None:
    op.drop_index("ix_answer_evaluations_answer_id", table_name="answer_evaluations")
    op.drop_table("answer_evaluations")
    op.drop_index("ix_candidate_answers_question_id", table_name="candidate_answers")
    op.drop_table("candidate_answers")
    op.drop_index("ix_interview_questions_session_id", table_name="interview_questions")
    op.drop_table("interview_questions")
    op.drop_index("ix_interview_sessions_job_id", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_resume_id", table_name="interview_sessions")
    op.drop_table("interview_sessions")
