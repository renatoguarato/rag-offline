from __future__ import annotations

import asyncio
import hashlib
from typing import Any, cast

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.application.ports import RetrievedChunk


class ChromaAdapter:
    def __init__(self, persist_directory: str) -> None:
        self._client = chromadb.PersistentClient(
            path=persist_directory, settings=ChromaSettings(anonymized_telemetry=False)
        )

    def _collection(self, tenant_id: str) -> chromadb.Collection:
        return self._client.get_or_create_collection(
            name=f"tenant_{tenant_id}", metadata={"tenant_id": tenant_id}
        )

    async def add(
        self, tenant_id: str, document_id: str, chunks: list[str], embeddings: list[list[float]]
    ) -> int:
        def write() -> int:
            hashes = [hashlib.sha256(chunk.encode()).hexdigest() for chunk in chunks]
            self._collection(tenant_id).add(
                ids=[f"{document_id}_{i}_{chunk_hash}" for i, chunk_hash in enumerate(hashes)],
                documents=chunks,
                embeddings=cast(Any, embeddings),
                metadatas=[
                    {"document_id": document_id, "chunk_index": i, "content_hash": h}
                    for i, h in enumerate(hashes)
                ],
            )
            return len(chunks)

        return await asyncio.to_thread(write)

    async def search(
        self, tenant_id: str, embedding: list[float], limit: int
    ) -> list[RetrievedChunk]:
        def read() -> list[RetrievedChunk]:
            results = cast(
                Any,
                self._collection(tenant_id).query(query_embeddings=[embedding], n_results=limit),
            )
            return [
                RetrievedChunk(
                    document_id=metadata["document_id"],
                    chunk_index=metadata["chunk_index"],
                    content=documents[i],
                    distance=distances[i],
                    content_hash=metadata.get(
                        "content_hash", hashlib.sha256(documents[i].encode()).hexdigest()
                    ),
                )
                for i, (metadata, documents, distances) in enumerate(
                    zip(
                        results["metadatas"][0],
                        results["documents"][0],
                        results["distances"][0],
                        strict=True,
                    )
                )
            ]

        return await asyncio.to_thread(read)

    async def delete_document(self, tenant_id: str, document_id: str) -> int:
        def delete() -> int:
            collection = self._collection(tenant_id)
            result = collection.get(where={"document_id": document_id})
            count = len(result["ids"])
            collection.delete(where={"document_id": document_id})
            return count

        return await asyncio.to_thread(delete)

    async def delete_tenant(self, tenant_id: str) -> int:
        def delete() -> int:
            collection = self._collection(tenant_id)
            result = collection.get()
            ids = result["ids"]
            if ids:
                collection.delete(ids=ids)
            return len(ids)

        return await asyncio.to_thread(delete)
