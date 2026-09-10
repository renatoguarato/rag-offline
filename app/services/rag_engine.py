from __future__ import annotations

from app.core.exceptions import RAGException
from app.core.logging import get_logger
from app.services.chroma_service import chroma_service
from app.services.document_processor import document_processor
from app.services.ollama_service import ollama_service

logger = get_logger(__name__)


class RAGEngine:
    async def index_document(
        self,
        tenant_id: str,
        document_id: str,
        content_type: str,
        file_content: bytes,
    ) -> int:
        try:
            text, chunks = document_processor.process_document(content_type, file_content)

            embeddings = await ollama_service.generate_embeddings(chunks)

            chroma_service.add_chunks(tenant_id, document_id, chunks, embeddings)

            logger.info(f"Indexed document {document_id} with {len(chunks)} chunks")
            return len(chunks)
        except Exception as e:
            logger.error(f"Failed to index document {document_id}: {e}")
            raise RAGException(f"Failed to index document: {e}")

    async def query(
        self,
        tenant_id: str,
        question: str,
        n_results: int = 5,
    ) -> dict:
        try:
            query_embedding = await ollama_service.generate_embeddings([question])

            results = chroma_service.query(tenant_id, query_embedding[0], n_results)

            context = "\n\n".join([result["content"] for result in results])

            answer = await ollama_service.generate_response(question, context)

            response = {
                "answer": answer,
                "sources": [
                    {
                        "document_id": result["document_id"],
                        "chunk_index": result["chunk_index"],
                        "content": result["content"],
                        "distance": result["distance"],
                    }
                    for result in results
                ],
                "context_chunks": len(results),
            }

            logger.info(f"Generated RAG response with {len(results)} context chunks")
            return response
        except Exception as e:
            logger.error(f"Failed to perform RAG query for tenant {tenant_id}: {e}")
            raise RAGException(f"Failed to perform RAG query: {e}")

    def delete_document(self, tenant_id: str, document_id: str) -> int:
        try:
            deleted_count = chroma_service.delete_document(tenant_id, document_id)
            logger.info(f"Deleted document {document_id} from vector store: {deleted_count} chunks")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise RAGException(f"Failed to delete document: {e}")

    def delete_tenant_data(self, tenant_id: str) -> int:
        try:
            deleted_count = chroma_service.delete_tenant_data(tenant_id)
            logger.info(
                f"Deleted tenant {tenant_id} data from vector store: {deleted_count} chunks"
            )
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete tenant {tenant_id} data: {e}")
            raise RAGException(f"Failed to delete tenant data: {e}")


rag_engine = RAGEngine()
