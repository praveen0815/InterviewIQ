from pathlib import Path
from uuid import uuid4
from zipfile import BadZipFile

import fitz
from docx import Document
from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.resume import Resume


def extract_pdf_text(file_path: Path) -> str:
    try:
        with fitz.open(file_path) as document:
            return "\n".join(page.get_text() for page in document).strip()
    except (OSError, RuntimeError, ValueError) as error:
        raise ValueError("Unable to extract text from the PDF file.") from error


def extract_docx_text(file_path: Path) -> str:
    try:
        document = Document(file_path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    except (OSError, ValueError, BadZipFile, KeyError) as error:
        raise ValueError("Unable to extract text from the DOCX file.") from error


def extract_text(file_path: Path, extension: str) -> str:
    if extension == ".pdf":
        return extract_pdf_text(file_path)
    if extension == ".docx":
        return extract_docx_text(file_path)
    raise ValueError("Unsupported resume file type.")


def save_resume(db: Session, upload: UploadFile, content: bytes, extension: str) -> Resume:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / f"{uuid4().hex}{extension}"

    try:
        stored_path.write_bytes(content)
        resume = Resume(
            original_filename=Path(upload.filename or "resume").name,
            file_type=extension.removeprefix("."),
            file_path=str(stored_path),
            extracted_text=extract_text(stored_path, extension),
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        return resume
    except (OSError, ValueError) as error:
        stored_path.unlink(missing_ok=True)
        raise ValueError(str(error)) from error
    except SQLAlchemyError:
        db.rollback()
        stored_path.unlink(missing_ok=True)
        raise


def get_resume(db: Session, resume_id: int) -> Resume | None:
    return db.get(Resume, resume_id)
