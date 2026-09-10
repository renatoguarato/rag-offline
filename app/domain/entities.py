from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.exceptions import InvalidDocumentState


@dataclass
class Tenant:
    id: str
    name: str
    api_key: str
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    def soft_delete(self, at: datetime) -> None:
        self.deleted_at = at
        self.updated_at = at


@dataclass
class Document:
    id: str
    tenant_id: str
    filename: str
    content_type: str
    file_size: int
    chunk_count: int
    index_status: str
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    def mark_indexed(self, chunk_count: int, at: datetime) -> None:
        if chunk_count < 1:
            raise InvalidDocumentState("An indexed document must contain chunks")
        self.chunk_count = chunk_count
        self.index_status = "indexed"
        self.updated_at = at

    def mark_failed(self, at: datetime) -> None:
        self.index_status = "failed"
        self.updated_at = at

    def soft_delete(self, at: datetime) -> None:
        self.deleted_at = at
        self.updated_at = at
