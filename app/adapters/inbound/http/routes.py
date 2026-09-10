from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.adapters.inbound.http.dependencies import (
    authenticated_tenant,
    document_use_cases,
    health_check,
    query_use_case,
    tenant_use_cases,
)
from app.adapters.inbound.http.schemas import (
    DocumentResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    TenantCreate,
    TenantCreatedResponse,
    TenantResponse,
)
from app.application.use_cases import DocumentUseCases, HealthCheck, QueryRAG, TenantUseCases
from app.bootstrap.config import Settings
from app.domain.entities import Tenant

SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


def build_router(settings: Settings) -> APIRouter:
    router = APIRouter()

    @router.get("/", tags=["root"])
    async def root() -> dict[str, str]:
        return {"name": "RAG Offline Multi-Tenant API", "version": "1.0.0", "status": "running"}

    tenants = APIRouter(prefix="/tenants", tags=["tenants"])

    @tenants.post("", response_model=TenantCreatedResponse, status_code=status.HTTP_201_CREATED)
    async def create_tenant(
        data: TenantCreate, service: TenantUseCases = Depends(tenant_use_cases)
    ) -> TenantCreatedResponse:
        return TenantCreatedResponse.from_domain(await service.create(data.name))

    @tenants.get("", response_model=list[TenantResponse])
    async def list_tenants(
        tenant: Tenant = Depends(authenticated_tenant),
        service: TenantUseCases = Depends(tenant_use_cases),
    ) -> list[TenantResponse]:
        return [TenantResponse.from_domain(value) for value in await service.list(0, 100)]

    @tenants.get("/{tenant_id}", response_model=TenantResponse)
    async def get_tenant(
        tenant_id: str, authenticated: Tenant = Depends(authenticated_tenant)
    ) -> TenantResponse:
        if authenticated.id != tenant_id:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return TenantResponse.from_domain(authenticated)

    @tenants.delete("/{tenant_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
    async def delete_tenant(
        tenant_id: str,
        authenticated: Tenant = Depends(authenticated_tenant),
        service: TenantUseCases = Depends(tenant_use_cases),
    ) -> None:
        if authenticated.id != tenant_id:
            raise HTTPException(status_code=404, detail="Tenant not found")
        await service.delete(tenant_id)

    documents = APIRouter(prefix="/documents", tags=["documents"])

    @documents.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
    async def upload_document(
        file: UploadFile,
        tenant: Tenant = Depends(authenticated_tenant),
        service: DocumentUseCases = Depends(document_use_cases),
    ) -> DocumentResponse:
        content_type = file.content_type or "application/octet-stream"
        if content_type not in SUPPORTED_CONTENT_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported document type")
        content = await file.read()
        if len(content) > settings.MAX_DOCUMENT_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_DOCUMENT_SIZE} bytes",
            )
        document = await service.upload(
            tenant.id, file.filename or "unnamed", content_type, content
        )
        return DocumentResponse.from_domain(document)

    @documents.get("", response_model=list[DocumentResponse])
    async def list_documents(
        tenant: Tenant = Depends(authenticated_tenant),
        service: DocumentUseCases = Depends(document_use_cases),
    ) -> list[DocumentResponse]:
        return [
            DocumentResponse.from_domain(value) for value in await service.list(tenant.id, 0, 100)
        ]

    @documents.get("/{document_id}", response_model=DocumentResponse)
    async def get_document(
        document_id: str,
        tenant: Tenant = Depends(authenticated_tenant),
        service: DocumentUseCases = Depends(document_use_cases),
    ) -> DocumentResponse:
        return DocumentResponse.from_domain(await service.get(tenant.id, document_id))

    @documents.delete("/{document_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
    async def delete_document(
        document_id: str,
        tenant: Tenant = Depends(authenticated_tenant),
        service: DocumentUseCases = Depends(document_use_cases),
    ) -> None:
        await service.delete(tenant.id, document_id)

    rag = APIRouter(prefix="/rag", tags=["rag"])

    @rag.post("/query", response_model=QueryResponse)
    async def query(
        data: QueryRequest,
        tenant: Tenant = Depends(authenticated_tenant),
        service: QueryRAG = Depends(query_use_case),
    ) -> QueryResponse:
        result = await service.execute(tenant.id, data.question, data.n_results)
        return QueryResponse(
            answer=result.answer,
            sources=[dict(source) for source in result.sources],
            context_chunks=result.context_chunks,
        )

    @router.get("/health", response_model=HealthResponse, tags=["health"])
    async def health(service: HealthCheck = Depends(health_check)) -> HealthResponse:
        connected = await service.execute()
        return HealthResponse(
            status="healthy" if connected else "degraded",
            ollama_connected=connected,
            timestamp=datetime.now(UTC),
        )

    router.include_router(tenants)
    router.include_router(documents)
    router.include_router(rag)
    return router
