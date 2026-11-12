from pathlib import Path
from zipfile import is_zipfile

from fastapi import HTTPException, UploadFile, status

ALLOWED_FILE_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def validate_resume_file(upload: UploadFile) -> str:
    extension = Path(upload.filename or "").suffix.lower()
    expected_mime = ALLOWED_FILE_TYPES.get(extension)
    if expected_mime is None or upload.content_type != expected_mime:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF and DOCX resume files are supported.",
        )
    return extension


def validate_resume_content(content: bytes, extension: str) -> None:
    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The uploaded file is not a valid PDF.",
        )
    if extension == ".docx":
        import io

        if not content.startswith(b"PK") or not is_zipfile(io.BytesIO(content)):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="The uploaded file is not a valid DOCX document.",
            )
