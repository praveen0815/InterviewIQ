"""add persisted interview reports

Revision ID: 20261112_0004
Revises: 20261112_0003
Create Date: 2026-11-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261112_0004"
down_revision: Union[str, None] = "20261112_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interview_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("interview_id", sa.Integer(), nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("report_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["interview_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["job_descriptions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("interview_id", name="uq_interview_report_interview"),
    )
    op.create_index("ix_interview_reports_interview_id", "interview_reports", ["interview_id"])
    op.create_index("ix_interview_reports_resume_id", "interview_reports", ["resume_id"])
    op.create_index("ix_interview_reports_job_id", "interview_reports", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_interview_reports_job_id", table_name="interview_reports")
    op.drop_index("ix_interview_reports_resume_id", table_name="interview_reports")
    op.drop_index("ix_interview_reports_interview_id", table_name="interview_reports")
    op.drop_table("interview_reports")
