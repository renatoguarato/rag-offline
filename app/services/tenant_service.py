from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TenantNotFoundException
from app.core.logging import get_logger
from app.models.tenant import Tenant

logger = get_logger(__name__)


def generate_api_key() -> str:
    return secrets.token_hex(32)


class TenantService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_tenant(self, name: str) -> Tenant:
        api_key = generate_api_key()

        tenant = Tenant(
            id=str(uuid.uuid4()),
            api_key=api_key,
            name=name,
        )

        self.db.add(tenant)
        await self.db.commit()
        await self.db.refresh(tenant)

        logger.info(f"Created tenant {tenant.id} with name: {name}")
        return tenant

    async def get_tenant(self, tenant_id: str) -> Tenant:
        result = await self.db.execute(
            select(Tenant).where(
                Tenant.id == tenant_id,
                Tenant.deleted_at.is_(None),
            ),
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            logger.warning(f"Tenant not found: {tenant_id}")
            raise TenantNotFoundException(f"Tenant not found: {tenant_id}")

        return tenant

    async def get_tenant_by_api_key(self, api_key: str) -> Tenant:
        result = await self.db.execute(
            select(Tenant).where(
                Tenant.api_key == api_key,
                Tenant.deleted_at.is_(None),
            ),
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            logger.warning(f"Tenant not found for API key: {api_key[:8]}...")
            raise TenantNotFoundException("Invalid API key")

        return tenant

    async def verify_tenant(self, tenant_id: str, api_key: str) -> Tenant:
        tenant = await self.get_tenant(tenant_id)

        if tenant.api_key != api_key:
            logger.warning(f"Invalid API key for tenant {tenant_id}")
            raise TenantNotFoundException("Invalid API key")

        return tenant

    async def list_tenants(self, skip: int = 0, limit: int = 100) -> list[Tenant]:
        result = await self.db.execute(
            select(Tenant).where(Tenant.deleted_at.is_(None)).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def delete_tenant(self, tenant_id: str) -> None:
        tenant = await self.get_tenant(tenant_id)
        tenant.deleted_at = datetime.now(UTC)
        await self.db.commit()

        logger.info(f"Soft deleted tenant {tenant_id}")
