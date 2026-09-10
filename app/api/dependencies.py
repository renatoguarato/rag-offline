from __future__ import annotations

from functools import lru_cache
from typing import cast

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.chroma import ChromaAdapter
from app.adapters.document_processing import DocumentProcessingAdapter
from app.adapters.ollama import (
    OllamaEmbeddingAdapter,
    OllamaLanguageModelAdapter,
)
from app.adapters.persistence.repositories import (
    SqlAlchemyDocumentRepository,
    SqlAlchemyTenantRepository,
)
from app.application.ports import DocumentRepository, TenantRepository
from app.application.use_cases import AuthenticateTenant, DocumentUseCases, QueryRAG, TenantUseCases
from app.core.config import settings
from app.core.database import get_db
from app.middleware.tenant_auth import get_tenant_context
from app.services.ollama_service import OllamaService


@lru_cache
def get_ollama_service() -> OllamaService:
    return OllamaService()


@lru_cache
def get_embedding_provider() -> OllamaEmbeddingAdapter:
    return OllamaEmbeddingAdapter(get_ollama_service())


@lru_cache
def get_language_model() -> OllamaLanguageModelAdapter:
    return OllamaLanguageModelAdapter(get_ollama_service())


@lru_cache
def get_vector_store() -> ChromaAdapter:
    return ChromaAdapter()


def get_tenant_use_cases(
    db: AsyncSession = Depends(get_db),
    vectors: ChromaAdapter = Depends(get_vector_store),
) -> TenantUseCases:
    repository = cast(TenantRepository, SqlAlchemyTenantRepository(db))
    return TenantUseCases(repository, vectors)


def get_document_use_cases(
    db: AsyncSession = Depends(get_db),
    embeddings: OllamaEmbeddingAdapter = Depends(get_embedding_provider),
    vectors: ChromaAdapter = Depends(get_vector_store),
) -> DocumentUseCases:
    return DocumentUseCases(
        cast(DocumentRepository, SqlAlchemyDocumentRepository(db)),
        DocumentProcessingAdapter(),
        embeddings,
        vectors,
    )


def get_query_use_case() -> QueryRAG:
    return QueryRAG(
        get_embedding_provider(),
        get_language_model(),
        get_vector_store(),
        max_distance=settings.RAG_MAX_DISTANCE,
    )


def get_ollama_provider() -> OllamaEmbeddingAdapter:
    return get_embedding_provider()


async def authenticated_tenant(db: AsyncSession = Depends(get_db)):
    context = get_tenant_context()
    try:
        return await AuthenticateTenant(
            cast(TenantRepository, SqlAlchemyTenantRepository(db))
        ).execute(context.tenant_id, context.api_key)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid tenant credentials"
        ) from exc
