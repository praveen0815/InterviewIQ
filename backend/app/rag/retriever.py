from typing import Any

from app.config.settings import settings
from app.rag.embedding_service import SentenceTransformerEmbeddingService
from app.rag.vector_store import ChromaVectorStore


class Retriever:
    def __init__(
        self,
        vector_store: ChromaVectorStore | None = None,
        embedding_service: SentenceTransformerEmbeddingService | None = None,
    ) -> None:
        self.vector_store = vector_store or ChromaVectorStore()
        self.embedding_service = embedding_service or SentenceTransformerEmbeddingService()

    def retrieve(
        self,
        question: str,
        resume_id: int,
        job_id: int | None = None,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        return self.vector_store.search(
            self.embedding_service.embed_query(question),
            top_k or settings.rag_top_k,
            resume_id,
            job_id,
        )
