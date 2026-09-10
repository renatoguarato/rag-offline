from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from app.application.ports import (
    DocumentProcessor,
    DocumentRepository,
    EmbeddingProvider,
    LanguageModel,
    Source,
    TenantRepository,
    VectorStore,
)
from app.core.exceptions import RAGException, TenantNotFoundException
from app.core.logging import get_logger

logger = get_logger(__name__)


class TenantUseCases:
    def __init__(self, tenants: TenantRepository, vectors: VectorStore) -> None:
        self.tenants, self.vectors = tenants, vectors

    async def create(self, name: str):
        return await self.tenants.create(name)

    async def get(self, tenant_id: str):
        return await self.tenants.get(tenant_id)

    async def list(self, skip: int, limit: int):
        return await self.tenants.list(skip, limit)

    async def delete(self, tenant_id: str) -> None:
        await self.tenants.get(tenant_id)
        await self.vectors.delete_tenant(tenant_id)
        await self.tenants.soft_delete(tenant_id)


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
    def __init__(
        self,
        documents: DocumentRepository,
        processor: DocumentProcessor,
        embeddings: EmbeddingProvider,
        vectors: VectorStore,
    ) -> None:
        self.documents, self.processor, self.embeddings, self.vectors = (
            documents,
            processor,
            embeddings,
            vectors,
        )

    async def upload(self, tenant_id: str, filename: str, content_type: str, content: bytes):
        processed = self.processor.process(content_type, content)
        document = await self.documents.create(tenant_id, filename, content_type, len(content))
        try:
            embeddings = await self.embeddings.embed(processed.chunks)
            await self.vectors.add(tenant_id, document.id, processed.chunks, embeddings)
            document = await self.documents.update_chunk_count(
                tenant_id=tenant_id, document_id=document.id, count=len(processed.chunks)
            )
            return await self.documents.update_index_status(tenant_id, document.id, "indexed")
        except Exception as exc:
            try:
                await self.documents.update_index_status(tenant_id, document.id, "failed")
            except Exception:
                pass
            raise RAGException("Failed to index document") from exc

    async def list(self, tenant_id: str, skip: int, limit: int):
        return await self.documents.list(tenant_id, skip, limit)

    async def get(self, tenant_id: str, document_id: str):
        return await self.documents.get(document_id, tenant_id)

    async def delete(self, tenant_id: str, document_id: str) -> None:
        await self.documents.get(document_id, tenant_id)
        await self.vectors.delete_document(tenant_id, document_id)
        await self.documents.soft_delete(document_id, tenant_id)


@dataclass(frozen=True)
class QueryResult:
    answer: str
    sources: list[Source]
    context_chunks: int


class QueryRAG:
    def __init__(
        self,
        embeddings: EmbeddingProvider,
        model: LanguageModel,
        vectors: VectorStore,
        max_distance: float | None = None,
    ) -> None:
        self.embeddings, self.model, self.vectors = embeddings, model, vectors
        self.max_distance = max_distance

    async def execute(self, tenant_id: str, question: str, n_results: int) -> QueryResult:
        started_at = perf_counter()
        try:
            chunks = await self.vectors.search(
                tenant_id, (await self.embeddings.embed([question]))[0], n_results
            )
            if self.max_distance is not None:
                chunks = [chunk for chunk in chunks if chunk.distance <= self.max_distance]

            if not chunks:
                return QueryResult(
                    answer="I could not find enough information in the provided documents.",
                    sources=[],
                    context_chunks=0,
                )

            context = "\n\n".join(chunk.content for chunk in chunks)
            answer = await self.model.answer(question, context)
            sources: list[Source] = [
                {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "distance": chunk.distance,
                    "content_hash": chunk.content_hash,
                }
                for chunk in chunks
            ]
            elapsed_ms = (perf_counter() - started_at) * 1000
            logger.info(
                "RAG query completed in %.2fms with %d context chunks",
                elapsed_ms,
                len(chunks),
            )
            return QueryResult(answer, sources, len(chunks))
        except Exception as exc:
            raise RAGException("Failed to perform RAG query") from exc
