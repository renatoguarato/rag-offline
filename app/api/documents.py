from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, UploadFile, status

from app.core.config import settings
from app.core.exceptions import ValidationException
from app.api.dependencies import authenticated_tenant, get_document_use_cases
from app.schemas.common import DocumentResponse
from app.application.use_cases import DocumentUseCases

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    tenant=Depends(authenticated_tenant),
    service: DocumentUseCases = Depends(get_document_use_cases),
) -> DocumentResponse:
    content_type = file.content_type or "application/octet-stream"

    file_content = await file.read()

    if len(file_content) > settings.MAX_DOCUMENT_SIZE:
        raise ValidationException(
            f"File size exceeds maximum allowed size of {settings.MAX_DOCUMENT_SIZE} bytes"
        )

    document = await service.upload(tenant.id, file.filename or "unnamed", content_type, file_content)

    return DocumentResponse.model_validate(document)


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    tenant=Depends(authenticated_tenant),
    service: DocumentUseCases = Depends(get_document_use_cases),
) -> List[DocumentResponse]:
    documents = await service.list(tenant.id, skip=skip, limit=limit)
    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    tenant=Depends(authenticated_tenant),
    service: DocumentUseCases = Depends(get_document_use_cases),
) -> DocumentResponse:
    document = await service.get(tenant.id, document_id)
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    tenant=Depends(authenticated_tenant),
    service: DocumentUseCases = Depends(get_document_use_cases),
):
    await service.delete(tenant.id, document_id)
