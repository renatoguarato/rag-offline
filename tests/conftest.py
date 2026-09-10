from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.adapters.persistence.repositories import (
    SqlAlchemyDocumentRepository,
    SqlAlchemyTenantRepository,
)
from app.api.dependencies import (
    get_document_use_cases,
    get_ollama_provider,
    get_query_use_case,
    get_tenant_use_cases,
)
from app.application.use_cases import DocumentUseCases, QueryRAG, TenantUseCases
from app.core.database import Base, get_db
from app.main import app
from tests.fakes import (
    FakeDocumentProcessor,
    FakeEmbeddingProvider,
    FakeLanguageModel,
    FakeVectorStore,
)

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = override_get_db
    embeddings = FakeEmbeddingProvider()
    model = FakeLanguageModel()
    vectors = FakeVectorStore()

    def override_documents(db: AsyncSession = Depends(get_db)) -> DocumentUseCases:
        return DocumentUseCases(
            SqlAlchemyDocumentRepository(db),
            FakeDocumentProcessor(),
            embeddings,
            vectors,
        )

    def override_query() -> QueryRAG:
        return QueryRAG(embeddings, model, vectors)

    def override_tenants(db: AsyncSession = Depends(get_db)) -> TenantUseCases:
        return TenantUseCases(SqlAlchemyTenantRepository(db), vectors)

    app.dependency_overrides[get_document_use_cases] = override_documents
    app.dependency_overrides[get_query_use_case] = override_query
    app.dependency_overrides[get_tenant_use_cases] = override_tenants
    app.dependency_overrides[get_ollama_provider] = lambda: embeddings

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def tenant_client(client: AsyncClient) -> AsyncClient:
    response = await client.post("/tenants", json={"name": "Test Tenant"})
    tenant_data = response.json()

    client.headers.update(
        {
            "X-Tenant-ID": tenant_data["id"],
            "X-API-KEY": tenant_data["api_key"],
        }
    )

    return client
