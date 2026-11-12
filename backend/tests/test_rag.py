from io import BytesIO

import fitz

from app.main import app
from app.rag.embedding_service import SentenceTransformerEmbeddingService
from app.rag.rag_service import RAGService
from app.rag.text_splitter import split_text
from app.routers.rag_router import get_rag_service
from app.services.llm_service import get_llm_service


class FakeEmbeddings:
    def embed_documents(self, texts):
        return [[float(len(text)), 1.0] for text in texts]

    def embed_query(self, text):
        return [float(len(text)), 1.0]


class FakeStore:
    def __init__(self):
        self.documents = {}
        self.replacements = 0

    def existing_hash(self, source_type, source_id):
        values = self.documents.get((source_type, source_id), [])
        return values[0]["metadata"]["content_hash"] if values else None

    def replace_document(self, source_type, source_id, filename, chunks, embeddings, content_hash):
        self.replacements += 1
        self.documents[(source_type, source_id)] = [
            {"text": chunk.text, "metadata": {"source_type": source_type, "source_id": str(source_id),
             "filename": filename, "chunk_index": chunk.index, "content_hash": content_hash},
             "distance": 0.1}
            for chunk in chunks
        ]
        return len(chunks)

    def search(self, query_embedding, top_k, resume_id, job_id=None):
        values = self.documents.get(("resume", resume_id), [])
        if job_id is not None:
            values += self.documents.get(("job", job_id), [])
        return values[:top_k]


class FakeLLM:
    def generate_text(self, prompt):
        return "The resume shows API development."


def make_pdf(text="Python developer with FastAPI experience"):
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def test_text_chunking_handles_empty_and_overlap():
    assert split_text("") == []
    chunks = split_text("one two three four five six", chunk_size=13, chunk_overlap=3)
    assert len(chunks) > 1
    assert all(chunk.text for chunk in chunks)


def test_rag_indexing_deduplicates_and_reindexes(client):
    store = FakeStore()
    service = RAGService(vector_store=store, embedding_service=FakeEmbeddings())
    app.dependency_overrides[get_rag_service] = lambda: service
    try:
        uploaded = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", make_pdf(), "application/pdf")},
        )
        resume_id = uploaded.json()["id"]
        first = client.post(f"/api/v1/rag/index/resume/{resume_id}")
        duplicate = client.post(f"/api/v1/rag/index/resume/{resume_id}")
        reindexed = client.post(f"/api/v1/rag/reindex/resume/{resume_id}")
        assert first.json()["chunks_indexed"] == 1
        assert duplicate.json()["duplicate"] is True
        assert reindexed.json()["reindexed"] is True
        assert store.replacements == 2
    finally:
        app.dependency_overrides.pop(get_rag_service, None)


def test_rag_query_returns_context_and_handles_missing_context(client):
    store = FakeStore()
    service = RAGService(vector_store=store, embedding_service=FakeEmbeddings())
    app.dependency_overrides[get_rag_service] = lambda: service
    app.dependency_overrides[get_llm_service] = lambda: FakeLLM()
    try:
        uploaded = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", make_pdf(), "application/pdf")},
        )
        resume_id = uploaded.json()["id"]
        client.post(f"/api/v1/rag/index/resume/{resume_id}")
        response = client.post(
            "/api/v1/rag/query",
            json={"resume_id": resume_id, "question": "Which API experience is listed?"},
        )
        assert response.status_code == 200
        assert response.json()["retrieved_context"][0]["metadata"]["source_type"] == "resume"
    finally:
        app.dependency_overrides.pop(get_rag_service, None)
        app.dependency_overrides.pop(get_llm_service, None)
