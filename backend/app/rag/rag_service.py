from typing import Any

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.rag.document_loader import load_job, load_resume
from app.rag.embedding_service import EmbeddingServiceError, SentenceTransformerEmbeddingService
from app.rag.retriever import Retriever
from app.rag.text_splitter import split_text
from app.rag.vector_store import ChromaVectorStore, VectorStoreError, document_hash
from app.services.llm_service import GeminiLLMService


class RAGServiceError(RuntimeError):
    pass


class RAGService:
    def __init__(
        self,
        vector_store: ChromaVectorStore | None = None,
        embedding_service: SentenceTransformerEmbeddingService | None = None,
        retriever: Retriever | None = None,
    ) -> None:
        store = vector_store or ChromaVectorStore()
        embeddings = embedding_service or SentenceTransformerEmbeddingService()
        self.vector_store = store
        self.embedding_service = embeddings
        self.retriever = retriever or Retriever(store, embeddings)

    def index_resume(self, db: Session, resume_id: int, force: bool = False) -> dict[str, Any]:
        resume = db.get(Resume, resume_id)
        if resume is None:
            raise LookupError("Resume not found.")
        return self._index(load_resume(resume), force)

    def index_job(self, db: Session, job_id: int, force: bool = False) -> dict[str, Any]:
        job = db.get(JobDescription, job_id)
        if job is None:
            raise LookupError("Job description not found.")
        return self._index(load_job(job), force)

    def _index(self, document: Any, force: bool) -> dict[str, Any]:
        if not document.text.strip():
            return {"source_type": document.source_type, "source_id": document.source_id, "chunks_indexed": 0}
        chunks = split_text(document.text)
        content_hash = document_hash(document.text)
        try:
            if not force and self.vector_store.existing_hash(
                document.source_type, document.source_id
            ) == content_hash:
                return {
                    "source_type": document.source_type,
                    "source_id": document.source_id,
                    "chunks_indexed": 0,
                    "content_hash": content_hash,
                    "duplicate": True,
                    "reindexed": False,
                }
            embeddings = self.embedding_service.embed_documents([chunk.text for chunk in chunks])
            count = self.vector_store.replace_document(
                document.source_type, document.source_id, document.filename, chunks, embeddings, content_hash
            )
        except (EmbeddingServiceError, VectorStoreError) as error:
            raise RAGServiceError(str(error)) from error
        return {
            "source_type": document.source_type,
            "source_id": document.source_id,
            "chunks_indexed": count,
            "content_hash": content_hash,
            "reindexed": force,
        }

    def query(
        self,
        db: Session,
        resume_id: int,
        question: str,
        llm_service: GeminiLLMService,
        job_id: int | None = None,
    ) -> dict[str, Any]:
        if db.get(Resume, resume_id) is None:
            raise LookupError("Resume not found.")
        if job_id is not None and db.get(JobDescription, job_id) is None:
            raise LookupError("Job description not found.")
        try:
            contexts = self.retriever.retrieve(question, resume_id, job_id)
            context_text = "\n\n".join(
                f"[{item['metadata'].get('source_type', 'document')}] {item['text']}" for item in contexts
            )
            if not context_text:
                answer = "The information is unavailable in the indexed documents."
            else:
                prompt = (
                    "Answer the question using only the supplied context. If the context does not contain "
                    "the answer, say exactly that the information is unavailable rather than guessing.\n\n"
                    f"CONTEXT:\n{context_text}\n\nQUESTION: {question}"
                )
                answer = llm_service.generate_text(prompt)
            return {
                "answer": answer,
                "retrieved_context": contexts,
                "source_documents": [item["metadata"] for item in contexts],
            }
        except (EmbeddingServiceError, VectorStoreError) as error:
            raise RAGServiceError(str(error)) from error
