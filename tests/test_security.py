from __future__ import annotations

from httpx import AsyncClient


async def test_protected_endpoint_requires_tenant_headers(client: AsyncClient) -> None:
    response = await client.get("/documents")

    assert response.status_code == 401


async def test_invalid_tenant_id_is_rejected(client: AsyncClient) -> None:
    response = await client.get(
        "/documents",
        headers={"X-Tenant-ID": "not-a-uuid", "X-API-KEY": "secret"},
    )

    assert response.status_code == 401
