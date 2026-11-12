from io import BytesIO

import fitz
from docx import Document


def make_pdf() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Python developer with FastAPI experience")
    content = document.tobytes()
    document.close()
    return content


def make_docx() -> bytes:
    document = Document()
    document.add_paragraph("Senior engineer experienced with PostgreSQL")
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def test_pdf_upload_extracts_text_and_persists_metadata(client) -> None:
    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.pdf", make_pdf(), "application/pdf")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["original_filename"] == "resume.pdf"
    assert payload["file_type"] == "pdf"
    assert "FastAPI" in payload["extracted_text"]
    assert "file_path" not in payload

    retrieved = client.get(f"/api/v1/resumes/{payload['id']}")
    assert retrieved.status_code == 200
    assert retrieved.json()["extracted_text"] == payload["extracted_text"]


def test_docx_upload_extracts_text(client) -> None:
    response = client.post(
        "/api/v1/resumes/upload",
        files={
            "file": (
                "resume.docx",
                make_docx(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 201
    assert "PostgreSQL" in response.json()["extracted_text"]


def test_invalid_file_type_is_rejected(client) -> None:
    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", b"not a resume", "text/plain")},
    )

    assert response.status_code == 415


def test_file_with_pdf_extension_but_invalid_signature_is_rejected(client) -> None:
    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.pdf", b"not a PDF", "application/pdf")},
    )

    assert response.status_code == 415


def test_empty_file_is_rejected(client) -> None:
    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400


def test_missing_resume_returns_not_found(client) -> None:
    response = client.get("/api/v1/resumes/999999")

    assert response.status_code == 404
