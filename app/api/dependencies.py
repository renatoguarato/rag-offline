from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.chroma import ChromaAdapter
from app.adapters.document_processing import DocumentProcessingAdapter
from app.adapters.ollama import OllamaAdapter
from app.adapters.persistence.repositories import SqlAlchemyDocumentRepository, SqlAlchemyTenantRepository
from app.application.use_cases import AuthenticateTenant, DocumentUseCases, QueryRAG, TenantUseCases
from app.core.database import get_db
from app.middleware.tenant_auth import get_tenant_context


def get_tenant_use_cases(db: AsyncSession = Depends(get_db)) -> TenantUseCases:
    return TenantUseCases(SqlAlchemyTenantRepository(db), ChromaAdapter())


def get_document_use_cases(db: AsyncSession = Depends(get_db)) -> DocumentUseCases:
    return DocumentUseCases(SqlAlchemyDocumentRepository(db), DocumentProcessingAdapter(), OllamaAdapter(), ChromaAdapter())


def get_query_use_case() -> QueryRAG:
    provider = OllamaAdapter()
    return QueryRAG(provider, provider, ChromaAdapter())


def get_ollama_provider() -> OllamaAdapter:
    return OllamaAdapter()


async def authenticated_tenant(db: AsyncSession = Depends(get_db)):
    context = get_tenant_context()
    try:
        return await AuthenticateTenant(SqlAlchemyTenantRepository(db)).execute(context.tenant_id, context.api_key)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid tenant credentials") from exc
