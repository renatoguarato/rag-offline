from __future__ import annotations

import asyncio
from typing import Any, cast

from app.application.ports import RetrievedChunk
from app.services.chroma_service import ChromaService


class ChromaAdapter:
    def __init__(self) -> None:
        self._service = ChromaService()

    async def add(
        self, tenant_id: str, document_id: str, chunks: list[str], embeddings: list[list[float]]
    ) -> int:
        return await asyncio.to_thread(
            self._service.add_chunks, tenant_id, document_id, chunks, embeddings
        )

    async def search(
        self, tenant_id: str, embedding: list[float], limit: int
    ) -> list[RetrievedChunk]:
        raw_chunks: list[dict[str, object]] = cast(
            list[dict[str, object]],
            await asyncio.to_thread(cast(Any, self._service).query, tenant_id, embedding, limit),
        )
        return [
            RetrievedChunk(
                document_id=cast(str, chunk["document_id"]),
                chunk_index=cast(int, chunk["chunk_index"]),
                content=cast(str, chunk["content"]),
                distance=cast(float, chunk["distance"]),
                content_hash=cast(str, chunk["content_hash"]),
            )
            for chunk in raw_chunks
        ]

    async def delete_document(self, tenant_id: str, document_id: str) -> int:
        return await asyncio.to_thread(self._service.delete_document, tenant_id, document_id)

    async def delete_tenant(self, tenant_id: str) -> int:
        return await asyncio.to_thread(self._service.delete_tenant_data, tenant_id)
