from __future__ import annotations

from app.application.ports import RetrievedChunk
from app.services.chroma_service import ChromaService


class ChromaAdapter:
    def __init__(self) -> None: self._service = ChromaService()
    def add(self, tenant_id: str, document_id: str, chunks: list[str], embeddings: list[list[float]]) -> int:
        return self._service.add_chunks(tenant_id, document_id, chunks, embeddings)
    def search(self, tenant_id: str, embedding: list[float], limit: int) -> list[RetrievedChunk]:
        return [RetrievedChunk(**chunk) for chunk in self._service.query(tenant_id, embedding, limit)]
    def delete_document(self, tenant_id: str, document_id: str) -> int: return self._service.delete_document(tenant_id, document_id)
    def delete_tenant(self, tenant_id: str) -> int: return self._service.delete_tenant_data(tenant_id)
