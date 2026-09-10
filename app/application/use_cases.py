from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from app.application.ports import (
    ApiKeyGenerator,
    Clock,
    DocumentProcessor,
    EmbeddingProvider,
    IdentifierGenerator,
    LanguageModel,
    Source,
    Telemetry,
    UnitOfWorkFactory,
    VectorStore,
)
from app.domain.entities import Document, Tenant


class ApplicationError(Exception):
    pass


class TenantNotFound(ApplicationError):
    pass


class DocumentNotFound(ApplicationError):
    pass


class InvalidTenantCredentials(ApplicationError):
    pass


class DocumentProcessingFailed(ApplicationError):
    pass


class RAGQueryFailed(ApplicationError):
    pass


@dataclass(frozen=True)
class QueryResult:
    answer: str
    sources: list[Source]
    context_chunks: int


class TenantUseCases:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        vectors: VectorStore,
        clock: Clock,
        identifiers: IdentifierGenerator,
        api_keys: ApiKeyGenerator,
    ) -> None:
        self._uow_factory = uow_factory
        self._vectors = vectors
        self._clock = clock
        self._identifiers = identifiers
        self._api_keys = api_keys

    async def create(self, name: str) -> Tenant:
        tenant = Tenant(
            id=self._identifiers.new_id(),
            name=name,
            api_key=self._api_keys.new_key(),
            created_at=self._clock.now(),
        )
        async with self._uow_factory() as uow:
            await uow.tenants.add(tenant)
            await uow.commit()
        return tenant

    async def get(self, tenant_id: str) -> Tenant:
        async with self._uow_factory() as uow:
            return await uow.tenants.get(tenant_id)

    async def list(self, skip: int, limit: int) -> list[Tenant]:
        async with self._uow_factory() as uow:
            return list(await uow.tenants.list(skip, limit))

    async def delete(self, tenant_id: str) -> None:
        async with self._uow_factory() as uow:
            await uow.tenants.get(tenant_id)
        await self._vectors.delete_tenant(tenant_id)
        async with self._uow_factory() as uow:
            await uow.tenants.soft_delete(tenant_id)
            await uow.commit()


class AuthenticateTenant:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, tenant_id: str, api_key: str) -> Tenant:
        try:
            async with self._uow_factory() as uow:
                tenant = await uow.tenants.get(tenant_id)
        except TenantNotFound as exc:
            raise InvalidTenantCredentials("Invalid tenant credentials") from exc
        if tenant.api_key != api_key:
            raise InvalidTenantCredentials("Invalid tenant credentials")
        return tenant


class DocumentUseCases:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        processor: DocumentProcessor,
        embeddings: EmbeddingProvider,
        vectors: VectorStore,
        clock: Clock,
        identifiers: IdentifierGenerator,
    ) -> None:
        self._uow_factory = uow_factory
        self._processor = processor
        self._embeddings = embeddings
        self._vectors = vectors
        self._clock = clock
        self._identifiers = identifiers

    async def upload(
        self, tenant_id: str, filename: str, content_type: str, content: bytes
    ) -> Document:
        document: Document | None = None
        try:
            processed = self._processor.process(content_type, content)
            document = Document(
                id=self._identifiers.new_id(),
                tenant_id=tenant_id,
                filename=filename,
                content_type=content_type,
                file_size=len(content),
                chunk_count=0,
                index_status="pending",
                created_at=self._clock.now(),
            )
            async with self._uow_factory() as uow:
                await uow.documents.add(document)
                await uow.commit()
            embeddings = await self._embeddings.embed(processed.chunks)
            await self._vectors.add(tenant_id, document.id, processed.chunks, embeddings)
            document.mark_indexed(len(processed.chunks), self._clock.now())
            async with self._uow_factory() as uow:
                await uow.documents.save(document)
                await uow.commit()
            return document
        except Exception as exc:
            if document is not None:
                document.mark_failed(self._clock.now())
                async with self._uow_factory() as uow:
                    await uow.documents.save(document)
                    await uow.commit()
            raise DocumentProcessingFailed("Failed to index document") from exc

    async def list(self, tenant_id: str, skip: int, limit: int) -> list[Document]:
        async with self._uow_factory() as uow:
            return list(await uow.documents.list(tenant_id, skip, limit))

    async def get(self, tenant_id: str, document_id: str) -> Document:
        async with self._uow_factory() as uow:
            return await uow.documents.get(document_id, tenant_id)

    async def delete(self, tenant_id: str, document_id: str) -> None:
        async with self._uow_factory() as uow:
            await uow.documents.get(document_id, tenant_id)
        await self._vectors.delete_document(tenant_id, document_id)
        async with self._uow_factory() as uow:
            await uow.documents.soft_delete(document_id, tenant_id)
            await uow.commit()


class QueryRAG:
    def __init__(
        self,
        embeddings: EmbeddingProvider,
        model: LanguageModel,
        vectors: VectorStore,
        telemetry: Telemetry,
        max_distance: float | None = None,
    ) -> None:
        self._embeddings = embeddings
        self._model = model
        self._vectors = vectors
        self._telemetry = telemetry
        self._max_distance = max_distance

    async def execute(self, tenant_id: str, question: str, n_results: int) -> QueryResult:
        started_at = perf_counter()
        try:
            chunks = await self._vectors.search(
                tenant_id, (await self._embeddings.embed([question]))[0], n_results
            )
            if self._max_distance is not None:
                chunks = [chunk for chunk in chunks if chunk.distance <= self._max_distance]
            if not chunks:
                return QueryResult(
                    "I could not find enough information in the provided documents.", [], 0
                )
            context = "\n\n".join(chunk.content for chunk in chunks)
            answer = await self._model.answer(question, context)
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
            self._telemetry.event(
                "rag.query.completed",
                elapsed_ms=(perf_counter() - started_at) * 1000,
                context_chunks=len(chunks),
            )
            return QueryResult(answer, sources, len(chunks))
        except Exception as exc:
            raise RAGQueryFailed("Failed to perform RAG query") from exc


class HealthCheck:
    def __init__(self, embeddings: EmbeddingProvider) -> None:
        self._embeddings = embeddings

    async def execute(self) -> bool:
        return await self._embeddings.is_available()
