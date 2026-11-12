from collections.abc import Sequence
from typing import Any

from app.config.settings import settings


class EmbeddingServiceError(RuntimeError):
    pass


class SentenceTransformerEmbeddingService:
    def __init__(self, model_name: str | None = None, model: Any = None) -> None:
        self.model_name = model_name or settings.rag_embedding_model
        self._model = model

    def _get_model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError as error:
                raise EmbeddingServiceError(
                    "Sentence Transformers is not installed."
                ) from error
            except Exception as error:
                raise EmbeddingServiceError("Unable to load the embedding model.") from error
        return self._model

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            embeddings = self._get_model().encode(list(texts), normalize_embeddings=True)
            return [embedding.tolist() for embedding in embeddings]
        except EmbeddingServiceError:
            raise
        except Exception as error:
            raise EmbeddingServiceError("Unable to generate document embeddings.") from error

    def embed_query(self, text: str) -> list[float]:
        embeddings = self.embed_documents([text])
        if not embeddings:
            raise EmbeddingServiceError("Unable to generate query embedding.")
        return embeddings[0]
