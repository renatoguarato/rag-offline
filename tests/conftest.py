from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.adapters.persistence.database import Base
from app.adapters.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.application.use_cases import (
    AuthenticateTenant,
    DocumentUseCases,
    HealthCheck,
    QueryRAG,
    TenantUseCases,
)
from app.bootstrap.runtime import SecureApiKeyGenerator, SystemClock, UuidGenerator
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


class TestRuntime:
    def __init__(self) -> None:
        self._vectors = FakeVectorStore()
        self._embeddings = FakeEmbeddingProvider()

        def factory():
            return SqlAlchemyUnitOfWork(AsyncSessionLocal)

        self.tenant_use_cases = TenantUseCases(
            factory, self._vectors, SystemClock(), UuidGenerator(), SecureApiKeyGenerator()
        )
        self.authenticator = AuthenticateTenant(factory)
        self.document_use_cases = DocumentUseCases(
            factory,
            FakeDocumentProcessor(),
            self._embeddings,
            self._vectors,
            SystemClock(),
            UuidGenerator(),
        )
        self.query_rag = QueryRAG(
            self._embeddings, FakeLanguageModel(), self._vectors, _NoopTelemetry()
        )
        self.health_check = HealthCheck(self._embeddings)

    async def close(self) -> None:
        return None


class _NoopTelemetry:
    def event(self, name: str, **attributes: object) -> None:
        return None


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
    app.state.runtime = TestRuntime()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


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
