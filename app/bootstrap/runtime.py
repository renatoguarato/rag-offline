from __future__ import annotations

import secrets
import uuid
from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime

from app.adapters.chroma import ChromaAdapter
from app.adapters.document_processing import DocumentProcessingAdapter
from app.adapters.ollama import OllamaEmbeddingAdapter, OllamaGateway, OllamaLanguageModelAdapter
from app.adapters.persistence.database import AsyncSessionLocal, close_database
from app.adapters.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.application.ports import UnitOfWork
from app.application.use_cases import (
    AuthenticateTenant,
    DocumentUseCases,
    HealthCheck,
    QueryRAG,
    TenantUseCases,
)
from app.bootstrap.config import Settings
from app.bootstrap.logging import telemetry


class Runtime:
    def __init__(self, settings: Settings) -> None:
        gateway = OllamaGateway(
            settings.OLLAMA_BASE_URL, settings.OLLAMA_MODEL, settings.OLLAMA_EMBEDDING_MODEL
        )
        vectors = ChromaAdapter(settings.CHROMA_PERSIST_DIRECTORY)
        self.tenant_use_cases = TenantUseCases(
            self.uow_factory,
            vectors,
            SystemClock(),
            UuidGenerator(),
            SecureApiKeyGenerator(),
        )
        self.authenticator = AuthenticateTenant(self.uow_factory)
        self.document_use_cases = DocumentUseCases(
            self.uow_factory,
            DocumentProcessingAdapter(),
            OllamaEmbeddingAdapter(gateway),
            vectors,
            SystemClock(),
            UuidGenerator(),
        )
        self.query_rag = QueryRAG(
            OllamaEmbeddingAdapter(gateway),
            OllamaLanguageModelAdapter(gateway),
            vectors,
            telemetry(),
            settings.RAG_MAX_DISTANCE,
        )
        self.health_check = HealthCheck(OllamaEmbeddingAdapter(gateway))

    def uow_factory(self) -> AbstractAsyncContextManager[UnitOfWork]:
        return SqlAlchemyUnitOfWork(AsyncSessionLocal)

    async def close(self) -> None:
        await close_database()


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class UuidGenerator:
    def new_id(self) -> str:
        return str(uuid.uuid4())


class SecureApiKeyGenerator:
    def new_key(self) -> str:
        return secrets.token_hex(32)


def build_runtime(settings: Settings) -> Runtime:
    return Runtime(settings)
