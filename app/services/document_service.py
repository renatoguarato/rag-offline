from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DocumentNotFoundException
from app.core.logging import get_logger
from app.models.document import Document

logger = get_logger(__name__)


class DocumentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_document(
        self,
        tenant_id: str,
        filename: str,
        content_type: str,
        file_size: int,
        chunk_count: int,
    ) -> Document:
        document = Document(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            chunk_count=chunk_count,
        )

        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Created document {document.id} for tenant {tenant_id}")
        return document

    async def get_document(self, document_id: str, tenant_id: str) -> Document:
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.tenant_id == tenant_id,
                Document.deleted_at.is_(None),
            ),
        )
        document = result.scalar_one_or_none()

        if not document:
            logger.warning(f"Document not found: {document_id}")
            raise DocumentNotFoundException(f"Document not found: {document_id}")

        return document

    async def list_documents(
        self,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Document]:
        result = await self.db.execute(
            select(Document)
            .where(
                Document.tenant_id == tenant_id,
                Document.deleted_at.is_(None),
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_document(self, document_id: str, tenant_id: str) -> None:
        document = await self.get_document(document_id, tenant_id)
        document.deleted_at = datetime.utcnow()
        await self.db.commit()

        logger.info(f"Soft deleted document {document_id} for tenant {tenant_id}")
