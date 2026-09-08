from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import authenticated_tenant, get_tenant_use_cases
from app.application.use_cases import TenantUseCases
from app.schemas.common import TenantCreate, TenantResponse

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    service: TenantUseCases = Depends(get_tenant_use_cases),
) -> TenantResponse:
    tenant = await service.create(tenant_data.name)
    return TenantResponse.model_validate(tenant)


@router.get("", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    authenticated=Depends(authenticated_tenant),
) -> List[TenantResponse]:
    tenants = [authenticated]
    return [TenantResponse.model_validate(tenant) for tenant in tenants]


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    authenticated=Depends(authenticated_tenant),
) -> TenantResponse:
    if authenticated.id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    tenant = authenticated
    return TenantResponse.model_validate(tenant)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    authenticated=Depends(authenticated_tenant),
    service: TenantUseCases = Depends(get_tenant_use_cases),
):
    if authenticated.id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    await service.delete(tenant_id)
