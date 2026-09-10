from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, TypedDict


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


class TenantRecord(Protocol):
    id: str
    api_key: str


class DocumentRecord(Protocol):
    id: str
    index_status: str


class Source(TypedDict):
    document_id: str
    chunk_index: int
    content: str
    distance: float
    content_hash: str


class TenantRepository(Protocol):
    async def create(self, name: str) -> TenantRecord: ...
    async def get(self, tenant_id: str) -> TenantRecord: ...
    async def get_by_api_key(self, api_key: str) -> TenantRecord: ...
    async def list(self, skip: int, limit: int) -> Sequence[TenantRecord]: ...
    async def soft_delete(self, tenant_id: str) -> None: ...


class DocumentRepository(Protocol):
    async def create(
        self, tenant_id: str, filename: str, content_type: str, file_size: int
    ) -> DocumentRecord: ...
    async def get(self, document_id: str, tenant_id: str) -> DocumentRecord: ...
    async def list(self, tenant_id: str, skip: int, limit: int) -> Sequence[DocumentRecord]: ...
    async def update_chunk_count(
        self, tenant_id: str, document_id: str, count: int
    ) -> DocumentRecord: ...
    async def update_index_status(
        self, tenant_id: str, document_id: str, status: str
    ) -> DocumentRecord: ...
    async def soft_delete(self, document_id: str, tenant_id: str) -> None: ...


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
