from dataclasses import dataclass

from app.config.settings import settings


@dataclass(frozen=True)
class TextChunk:
    text: str
    index: int


def split_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[TextChunk]:
    size = chunk_size or settings.rag_chunk_size
    overlap = settings.rag_chunk_overlap if chunk_overlap is None else chunk_overlap
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Chunk size must be positive and overlap must be smaller than chunk size.")
    normalized = " ".join(text.split())
    if not normalized:
        return []
    chunks: list[TextChunk] = []
    start = 0
    while start < len(normalized):
        end = min(start + size, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start, end)
            if boundary > start + size // 2:
                end = boundary
        chunks.append(TextChunk(normalized[start:end].strip(), len(chunks)))
        if end == len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks
