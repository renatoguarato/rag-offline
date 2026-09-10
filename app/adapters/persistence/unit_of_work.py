from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.persistence.repositories import (
    SqlAlchemyDocumentRepository,
    SqlAlchemyTenantRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self.tenants: Any = None
        self.documents: Any = None

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self.tenants = SqlAlchemyTenantRepository(self._session)
        self.documents = SqlAlchemyDocumentRepository(self._session)
        return self

    async def __aexit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        if exc_type is not None:
            await self.rollback()
        if self._session is not None:
            await self._session.close()

    async def commit(self) -> None:
        if self._session is not None:
            await self._session.commit()

    async def rollback(self) -> None:
        if self._session is not None:
            await self._session.rollback()
