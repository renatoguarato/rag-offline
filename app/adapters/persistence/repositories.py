from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.persistence.models import DocumentModel, TenantModel
from app.application.use_cases import DocumentNotFound, TenantNotFound
from app.domain.entities import Document, Tenant


def _tenant(model: TenantModel) -> Tenant:
    return Tenant(
        model.id, model.name, model.api_key, model.created_at, model.updated_at, model.deleted_at
    )


def _document(model: DocumentModel) -> Document:
    return Document(
        model.id,
        model.tenant_id,
        model.filename,
        model.content_type,
        model.file_size,
        model.chunk_count,
        model.index_status,
        model.created_at,
        model.updated_at,
        model.deleted_at,
    )


class SqlAlchemyTenantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, tenant: Tenant) -> Tenant:
        self._session.add(
            TenantModel(
                id=tenant.id,
                name=tenant.name,
                api_key=tenant.api_key,
                created_at=tenant.created_at,
                updated_at=tenant.updated_at,
                deleted_at=tenant.deleted_at,
            )
        )
        return tenant

    async def get(self, tenant_id: str) -> Tenant:
        result = await self._session.execute(
            select(TenantModel).where(TenantModel.id == tenant_id, TenantModel.deleted_at.is_(None))
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise TenantNotFound("Tenant not found")
        return _tenant(model)

    async def list(self, skip: int, limit: int) -> list[Tenant]:
        result = await self._session.execute(
            select(TenantModel).where(TenantModel.deleted_at.is_(None)).offset(skip).limit(limit)
        )
        return [_tenant(model) for model in result.scalars().all()]

    async def soft_delete(self, tenant_id: str) -> None:
        result = await self._session.execute(select(TenantModel).where(TenantModel.id == tenant_id))
        model = result.scalar_one_or_none()
        if model is None:
            raise TenantNotFound("Tenant not found")
        model.deleted_at = datetime.now(UTC)


class SqlAlchemyDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, document: Document) -> Document:
        self._session.add(
            DocumentModel(
                id=document.id,
                tenant_id=document.tenant_id,
                filename=document.filename,
                content_type=document.content_type,
                file_size=document.file_size,
                chunk_count=document.chunk_count,
                index_status=document.index_status,
                created_at=document.created_at,
                updated_at=document.updated_at,
                deleted_at=document.deleted_at,
            )
        )
        return document

    async def get(self, document_id: str, tenant_id: str) -> Document:
        result = await self._session.execute(
            select(DocumentModel).where(
                DocumentModel.id == document_id,
                DocumentModel.tenant_id == tenant_id,
                DocumentModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise DocumentNotFound("Document not found")
        return _document(model)

    async def list(self, tenant_id: str, skip: int, limit: int) -> list[Document]:
        result = await self._session.execute(
            select(DocumentModel)
            .where(DocumentModel.tenant_id == tenant_id, DocumentModel.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        return [_document(model) for model in result.scalars().all()]

    async def save(self, document: Document) -> Document:
        result = await self._session.execute(
            select(DocumentModel).where(DocumentModel.id == document.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise DocumentNotFound("Document not found")
        model.chunk_count = document.chunk_count
        model.index_status = document.index_status
        model.updated_at = document.updated_at
        model.deleted_at = document.deleted_at
        return document

    async def soft_delete(self, document_id: str, tenant_id: str) -> None:
        document = await self.get(document_id, tenant_id)
        document.soft_delete(datetime.now(UTC))
        await self.save(document)
