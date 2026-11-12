from dataclasses import dataclass

from app.models.job_description import JobDescription
from app.models.resume import Resume


@dataclass(frozen=True)
class LoadedDocument:
    source_type: str
    source_id: int
    text: str
    filename: str


def load_resume(resume: Resume) -> LoadedDocument:
    return LoadedDocument("resume", resume.id, resume.extracted_text or "", resume.original_filename)


def load_job(job: JobDescription) -> LoadedDocument:
    return LoadedDocument("job", job.id, job.description or "", f"job-{job.id}")
