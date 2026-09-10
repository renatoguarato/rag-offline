from __future__ import annotations

from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, TypedDict

from app.domain.entities import Document, Tenant


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    chunk_index: int
    content: str
    distance: float
    content_hash: str


@dataclass(frozen=True)
class ProcessedDocument:
    chunks: list[str]


class Source(TypedDict):
    document_id: str
    chunk_index: int
    content: str
    distance: float
    content_hash: str


class TenantRepository(Protocol):
    async def add(self, tenant: Tenant) -> Tenant: ...
    async def get(self, tenant_id: str) -> Tenant: ...
    async def list(self, skip: int, limit: int) -> Sequence[Tenant]: ...
    async def soft_delete(self, tenant_id: str) -> None: ...


class DocumentRepository(Protocol):
    async def add(self, document: Document) -> Document: ...
    async def get(self, document_id: str, tenant_id: str) -> Document: ...
    async def list(self, tenant_id: str, skip: int, limit: int) -> Sequence[Document]: ...
    async def save(self, document: Document) -> Document: ...
    async def soft_delete(self, document_id: str, tenant_id: str) -> None: ...


class UnitOfWork(Protocol):
    tenants: TenantRepository
    documents: DocumentRepository

    async def __aenter__(self) -> UnitOfWork: ...
    async def __aexit__(self, exc_type: object, exc_value: object, traceback: object) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> AbstractAsyncContextManager[UnitOfWork]: ...


class DocumentProcessor(Protocol):
    def process(self, content_type: str, content: bytes) -> ProcessedDocument: ...


class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
    async def is_available(self) -> bool: ...


class LanguageModel(Protocol):
    async def answer(self, question: str, context: str) -> str: ...


class VectorStore(Protocol):
    async def add(
        self, tenant_id: str, document_id: str, chunks: list[str], embeddings: list[list[float]]
    ) -> int: ...
    async def search(
        self, tenant_id: str, embedding: list[float], limit: int
    ) -> list[RetrievedChunk]: ...
    async def delete_document(self, tenant_id: str, document_id: str) -> int: ...
    async def delete_tenant(self, tenant_id: str) -> int: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class IdentifierGenerator(Protocol):
    def new_id(self) -> str: ...


class ApiKeyGenerator(Protocol):
    def new_key(self) -> str: ...


class Telemetry(Protocol):
    def event(self, name: str, **attributes: object) -> None: ...
