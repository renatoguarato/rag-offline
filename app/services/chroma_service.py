from __future__ import annotations

import hashlib
from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.core.exceptions import ChromaException
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChromaService:
    def __init__(self) -> None:
        try:
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info("ChromaDB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise ChromaException(f"Failed to initialize ChromaDB: {e}")

    def get_collection(self, tenant_id: str) -> chromadb.Collection:
        collection_name = f"tenant_{tenant_id}"
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"tenant_id": tenant_id},
            )
            return collection
        except Exception as e:
            logger.error(f"Failed to get collection for tenant {tenant_id}: {e}")
            raise ChromaException(f"Failed to get collection: {e}")

    def add_chunks(
        self,
        tenant_id: str,
        document_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
    ) -> int:
        collection = self.get_collection(tenant_id)

        ids = []
        for i, chunk in enumerate(chunks):
            chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
            ids.append(f"{document_id}_{i}_{chunk_hash}")

        metadatas = [{"document_id": document_id, "chunk_index": i} for i in range(len(chunks))]

        try:
            collection.add(
                ids=ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            logger.info(f"Added {len(chunks)} chunks for document {document_id}")
            return len(chunks)
        except Exception as e:
            logger.error(f"Failed to add chunks for document {document_id}: {e}")
            raise ChromaException(f"Failed to add chunks: {e}")

    def delete_document(self, tenant_id: str, document_id: str) -> int:
        collection = self.get_collection(tenant_id)

        try:
            result = collection.get(where={"document_id": document_id})
            deleted_count = len(result["ids"])

            collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete chunks for document {document_id}: {e}")
            raise ChromaException(f"Failed to delete chunks: {e}")

    def delete_tenant_data(self, tenant_id: str) -> int:
        collection = self.get_collection(tenant_id)

        try:
            result = collection.get()
            deleted_count = len(result["ids"])

            collection.delete(where={})
            logger.info(f"Deleted {deleted_count} chunks for tenant {tenant_id}")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete tenant {tenant_id} data: {e}")
            raise ChromaException(f"Failed to delete tenant data: {e}")

    def query(
        self,
        tenant_id: str,
        query_embedding: List[float],
        n_results: int = 5,
    ) -> List[dict]:
        collection = self.get_collection(tenant_id)

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
            )

            formatted_results = []
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "document_id": results["metadatas"][0][i]["document_id"],
                    "chunk_index": results["metadatas"][0][i]["chunk_index"],
                    "content": results["documents"][0][i],
                    "distance": results["distances"][0][i],
                })

            logger.info(f"Retrieved {len(formatted_results)} chunks for tenant {tenant_id}")
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to query ChromaDB for tenant {tenant_id}: {e}")
            raise ChromaException(f"Failed to query: {e}")

    def count_chunks(self, tenant_id: str, document_id: Optional[str] = None) -> int:
        collection = self.get_collection(tenant_id)

        try:
            if document_id:
                result = collection.get(where={"document_id": document_id})
            else:
                result = collection.get()
            return len(result["ids"])
        except Exception as e:
            logger.error(f"Failed to count chunks for tenant {tenant_id}: {e}")
            raise ChromaException(f"Failed to count chunks: {e}")


chroma_service = ChromaService()
