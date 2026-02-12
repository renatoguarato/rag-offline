from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.middleware.tenant_auth import get_tenant_context
from app.schemas.common import TenantCreate, TenantResponse
from app.services.tenant_service import TenantService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    service = TenantService(db)
    tenant = await service.create_tenant(tenant_data.name)
    return TenantResponse.model_validate(tenant)


@router.get("", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> List[TenantResponse]:
    service = TenantService(db)
    tenants = await service.list_tenants(skip=skip, limit=limit)
    return [TenantResponse.model_validate(tenant) for tenant in tenants]


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    service = TenantService(db)
    tenant = await service.get_tenant(tenant_id)
    return TenantResponse.model_validate(tenant)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
):
    from app.services.rag_engine import rag_engine

    service = TenantService(db)
    tenant = await service.get_tenant(tenant_id)

    rag_engine.delete_tenant_data(tenant_id)

    await service.delete_tenant(tenant_id)
