import hashlib
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.rag.text_splitter import TextChunk


class VectorStoreError(RuntimeError):
    pass


class ChromaVectorStore:
    collection_name = "interviewiq_documents"

    def __init__(self, persist_directory: str | None = None, client: Any = None) -> None:
        self.persist_directory = persist_directory or settings.rag_chroma_dir
        self._client = client
        self._collection = None

    def _get_collection(self) -> Any:
        if self._collection is None:
            try:
                import chromadb
                if self._client is None:
                    Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
                    self._client = chromadb.PersistentClient(path=self.persist_directory)
                self._collection = self._client.get_or_create_collection(
                    self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            except ImportError as error:
                raise VectorStoreError("ChromaDB is not installed.") from error
            except Exception as error:
                raise VectorStoreError("Unable to open the ChromaDB collection.") from error
        return self._collection

    @staticmethod
    def _where(source_type: str, source_id: int) -> dict[str, Any]:
        key = "resume_id" if source_type == "resume" else "job_id"
        return {key: str(source_id)}

    def replace_document(
        self,
        source_type: str,
        source_id: int,
        filename: str,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
        content_hash: str,
    ) -> int:
        collection = self._get_collection()
        where = self._where(source_type, source_id)
        collection.delete(where=where)
        if not chunks:
            return 0
        ids = [f"{source_type}:{source_id}:{chunk.index}" for chunk in chunks]
        metadata = [
            {
                "source_type": source_type,
                "source_id": str(source_id),
                "resume_id": str(source_id) if source_type == "resume" else "",
                "job_id": str(source_id) if source_type == "job" else "",
                "filename": filename,
                "chunk_index": chunk.index,
                "content_hash": content_hash,
            }
            for chunk in chunks
        ]
        collection.upsert(
            ids=ids,
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=metadata,
        )
        return len(chunks)

    def existing_hash(self, source_type: str, source_id: int) -> str | None:
        result = self._get_collection().get(
            where=self._where(source_type, source_id),
            include=["metadatas"],
        )
        metadatas = result.get("metadatas", [])
        return metadatas[0].get("content_hash") if metadatas and metadatas[0] else None

    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        resume_id: int,
        job_id: int | None = None,
    ) -> list[dict[str, Any]]:
        where: dict[str, Any] = {"resume_id": str(resume_id)}
        if job_id is not None:
            where = {"$or": [{"resume_id": str(resume_id)}, {"job_id": str(job_id)}]}
        result = self._get_collection().query(
            query_embeddings=[query_embedding],
            n_results=max(1, top_k),
            where=where,
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            {"text": text, "metadata": metadata or {}, "distance": distances[index]}
            for index, text in enumerate(documents)
        ]


def document_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
