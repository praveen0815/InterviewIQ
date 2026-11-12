from pathlib import Path

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
