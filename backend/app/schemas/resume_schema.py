from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    original_filename: str
    file_type: str
    extracted_text: str
    created_at: datetime
    updated_at: datetime


class ResumeUploadResponse(ResumeResponse):
    message: str = "Resume uploaded successfully"
