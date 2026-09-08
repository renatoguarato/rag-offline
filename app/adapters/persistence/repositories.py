from __future__ import annotations

import secrets
import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DocumentNotFoundException, TenantNotFoundException
from app.models.document import Document
from app.models.tenant import Tenant


class SqlAlchemyTenantRepository:
    def __init__(self, session: AsyncSession) -> None: self.session = session
    async def create(self, name: str) -> Tenant:
        tenant = Tenant(id=str(uuid.uuid4()), api_key=secrets.token_hex(32), name=name)
        self.session.add(tenant); await self.session.commit(); await self.session.refresh(tenant)
        return tenant
    async def get(self, tenant_id: str) -> Tenant:
        result = await self.session.execute(select(Tenant).where(Tenant.id == tenant_id, Tenant.deleted_at.is_(None)))
        tenant = result.scalar_one_or_none()
        if tenant is None: raise TenantNotFoundException("Tenant not found")
        return tenant
    async def get_by_api_key(self, api_key: str) -> Tenant:
        result = await self.session.execute(select(Tenant).where(Tenant.api_key == api_key, Tenant.deleted_at.is_(None)))
        tenant = result.scalar_one_or_none()
        if tenant is None: raise TenantNotFoundException("Invalid API key")
        return tenant
    async def list(self, skip: int, limit: int):
        result = await self.session.execute(select(Tenant).where(Tenant.deleted_at.is_(None)).offset(skip).limit(limit))
        return list(result.scalars().all())
    async def soft_delete(self, tenant_id: str) -> None:
        tenant = await self.get(tenant_id); tenant.deleted_at = datetime.utcnow(); await self.session.commit()


class SqlAlchemyDocumentRepository:
    def __init__(self, session: AsyncSession) -> None: self.session = session
    async def create(self, tenant_id: str, filename: str, content_type: str, file_size: int) -> Document:
        document = Document(id=str(uuid.uuid4()), tenant_id=tenant_id, filename=filename, content_type=content_type, file_size=file_size, chunk_count=0)
        self.session.add(document); await self.session.commit(); await self.session.refresh(document)
        return document
    async def get(self, document_id: str, tenant_id: str) -> Document:
        result = await self.session.execute(select(Document).where(Document.id == document_id, Document.tenant_id == tenant_id, Document.deleted_at.is_(None)))
        document = result.scalar_one_or_none()
        if document is None: raise DocumentNotFoundException("Document not found")
        return document
    async def list(self, tenant_id: str, skip: int, limit: int):
        result = await self.session.execute(select(Document).where(Document.tenant_id == tenant_id, Document.deleted_at.is_(None)).offset(skip).limit(limit))
        return list(result.scalars().all())
    async def update_chunk_count(self, tenant_id: str, document_id: str, count: int) -> Document:
        document = await self.get(document_id, tenant_id); document.chunk_count = count
        await self.session.commit(); await self.session.refresh(document); return document
    async def soft_delete(self, document_id: str, tenant_id: str) -> None:
        document = await self.get(document_id, tenant_id); document.deleted_at = datetime.utcnow(); await self.session.commit()
