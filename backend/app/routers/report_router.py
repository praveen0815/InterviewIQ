from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.connection import get_db
from app.schemas.report_schema import (
    DashboardSummaryResponse,
    InterviewReportResponse,
    ReportListResponse,
)
from app.services.report_service import ReportService

router = APIRouter(prefix=settings.api_v1_prefix, tags=["reports"])


def get_report_service() -> ReportService:
    return ReportService()


@router.get("/reports/{report_id}", response_model=InterviewReportResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    service: ReportService = Depends(get_report_service),
) -> InterviewReportResponse:
    try:
        return service.response(service.get(db, report_id))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/reports/{report_id}/pdf")
def download_report_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    service: ReportService = Depends(get_report_service),
) -> Response:
    try:
        report = service.get(db, report_id)
        return Response(
            content=service.pdf(report),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="interview-report-{report.id}.pdf"'},
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/interviews/{interview_id}/report", response_model=InterviewReportResponse)
def get_interview_report(
    interview_id: int,
    db: Session = Depends(get_db),
    service: ReportService = Depends(get_report_service),
) -> InterviewReportResponse:
    try:
        return service.response(service.get_for_interview(db, interview_id))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/reports", response_model=ReportListResponse)
def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    resume_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    service: ReportService = Depends(get_report_service),
) -> ReportListResponse:
    return service.list_reports(db, page, page_size, resume_id)


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    page_size: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    service: ReportService = Depends(get_report_service),
) -> DashboardSummaryResponse:
    return service.dashboard(db, page_size)
