from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ValidationException
from app.middleware.tenant_auth import get_tenant_context
from app.schemas.common import DocumentResponse
from app.services.document_service import DocumentService
from app.services.rag_engine import rag_engine
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    context = get_tenant_context()

    content_type = file.content_type or "application/octet-stream"

    file_content = await file.read()

    if len(file_content) > settings.MAX_DOCUMENT_SIZE:
        raise ValidationException(
            f"File size exceeds maximum allowed size of {settings.MAX_DOCUMENT_SIZE} bytes"
        )

    service = DocumentService(db)
    document = await service.create_document(
        tenant_id=context.tenant_id,
        filename=file.filename,
        content_type=content_type,
        file_size=len(file_content),
        chunk_count=0,
    )

    chunk_count = await rag_engine.index_document(
        tenant_id=context.tenant_id,
        document_id=document.id,
        content_type=content_type,
        file_content=file_content,
    )

    document.chunk_count = chunk_count
    await db.commit()
    await db.refresh(document)

    return DocumentResponse.model_validate(document)


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> List[DocumentResponse]:
    context = get_tenant_context()

    service = DocumentService(db)
    documents = await service.list_documents(context.tenant_id, skip=skip, limit=limit)
    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    context = get_tenant_context()

    service = DocumentService(db)
    document = await service.get_document(document_id, context.tenant_id)
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    context = get_tenant_context()

    service = DocumentService(db)
    document = await service.get_document(document_id, context.tenant_id)

    rag_engine.delete_document(context.tenant_id, document_id)

    await service.delete_document(document_id, context.tenant_id)
