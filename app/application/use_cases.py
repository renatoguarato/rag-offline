from __future__ import annotations

from dataclasses import dataclass

from app.application.ports import DocumentProcessor, DocumentRepository, EmbeddingProvider, LanguageModel, TenantRepository, VectorStore
from app.core.exceptions import RAGException, TenantNotFoundException


class TenantUseCases:
    def __init__(self, tenants: TenantRepository, vectors: VectorStore) -> None:
        self.tenants, self.vectors = tenants, vectors

    async def create(self, name: str): return await self.tenants.create(name)
    async def get(self, tenant_id: str): return await self.tenants.get(tenant_id)
    async def list(self, skip: int, limit: int): return await self.tenants.list(skip, limit)

    async def delete(self, tenant_id: str) -> None:
        await self.tenants.get(tenant_id)
        self.vectors.delete_tenant(tenant_id)
        await self.tenants.soft_delete(tenant_id)

    async def authenticate(self, tenant_id: str, api_key: str):
        tenant = await self.tenants.get(tenant_id)
        if tenant.api_key != api_key:
            raise TenantNotFoundException("Invalid API key")
        return tenant


class AuthenticateTenant:
    """Application service for credential verification without storage coupling."""

    def __init__(self, tenants: TenantRepository) -> None:
        self.tenants = tenants

    async def execute(self, tenant_id: str, api_key: str):
        tenant = await self.tenants.get(tenant_id)
        if tenant.api_key != api_key:
            raise TenantNotFoundException("Invalid API key")
        return tenant


class DocumentUseCases:
    def __init__(self, documents: DocumentRepository, processor: DocumentProcessor, embeddings: EmbeddingProvider, vectors: VectorStore) -> None:
        self.documents, self.processor, self.embeddings, self.vectors = documents, processor, embeddings, vectors

    async def upload(self, tenant_id: str, filename: str, content_type: str, content: bytes):
        processed = self.processor.process(content_type, content)
        document = await self.documents.create(tenant_id, filename, content_type, len(content))
        try:
            embeddings = await self.embeddings.embed(processed.chunks)
            self.vectors.add(tenant_id, document.id, processed.chunks, embeddings)
            return await self.documents.update_chunk_count(tenant_id=tenant_id, document_id=document.id, count=len(processed.chunks))
        except Exception as exc:
            raise RAGException("Failed to index document") from exc

    async def list(self, tenant_id: str, skip: int, limit: int): return await self.documents.list(tenant_id, skip, limit)
    async def get(self, tenant_id: str, document_id: str): return await self.documents.get(document_id, tenant_id)

    async def delete(self, tenant_id: str, document_id: str) -> None:
        await self.documents.get(document_id, tenant_id)
        self.vectors.delete_document(tenant_id, document_id)
        await self.documents.soft_delete(document_id, tenant_id)


@dataclass(frozen=True)
class QueryResult:
    answer: str
    sources: list[dict]
    context_chunks: int


class QueryRAG:
    def __init__(self, embeddings: EmbeddingProvider, model: LanguageModel, vectors: VectorStore) -> None:
        self.embeddings, self.model, self.vectors = embeddings, model, vectors

    async def execute(self, tenant_id: str, question: str, n_results: int) -> QueryResult:
        try:
            chunks = self.vectors.search(tenant_id, (await self.embeddings.embed([question]))[0], n_results)
            context = "\n\n".join(chunk.content for chunk in chunks)
            answer = await self.model.answer(question, context)
            sources = [chunk.__dict__ for chunk in chunks]
            return QueryResult(answer, sources, len(chunks))
        except Exception as exc:
            raise RAGException("Failed to perform RAG query") from exc
