from __future__ import annotations

from app.application.ports import ProcessedDocument, RetrievedChunk


class FakeEmbeddingProvider:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0] for _ in texts]

    async def is_available(self) -> bool:
        return True


class FakeLanguageModel:
    async def answer(self, question: str, context: str) -> str:
        return f"Answer for: {question}"


class FakeDocumentProcessor:
    def process(self, content_type: str, content: bytes) -> ProcessedDocument:
        return ProcessedDocument([content.decode("utf-8")])


class FakeVectorStore:
    def __init__(self) -> None:
        self._chunks: dict[str, list[RetrievedChunk]] = {}

    async def add(
        self, tenant_id: str, document_id: str, chunks: list[str], embeddings: list[list[float]]
    ) -> int:
        self._chunks.setdefault(tenant_id, []).extend(
            RetrievedChunk(document_id, index, content, 0.1, f"hash-{document_id}-{index}")
            for index, content in enumerate(chunks)
        )
        return len(chunks)

    async def search(
        self, tenant_id: str, embedding: list[float], limit: int
    ) -> list[RetrievedChunk]:
        return self._chunks.get(tenant_id, [])[:limit]

    async def delete_document(self, tenant_id: str, document_id: str) -> int:
        chunks = self._chunks.get(tenant_id, [])
        remaining = [chunk for chunk in chunks if chunk.document_id != document_id]
        self._chunks[tenant_id] = remaining
        return len(chunks) - len(remaining)

    async def delete_tenant(self, tenant_id: str) -> int:
        deleted = len(self._chunks.get(tenant_id, []))
        self._chunks.pop(tenant_id, None)
        return deleted
