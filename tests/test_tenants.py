from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_tenant(client: AsyncClient) -> None:
    response = await client.post("/tenants", json={"name": "Test Tenant"})

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Tenant"
    assert "api_key" in data
    assert len(data["api_key"]) == 64


@pytest.mark.asyncio
async def test_list_tenants(client: AsyncClient) -> None:
    create_response = await client.post("/tenants", json={"name": "Tenant 1"})
    tenant_data = create_response.json()
    client.headers.update({"X-Tenant-ID": tenant_data["id"], "X-API-KEY": tenant_data["api_key"]})

    response = await client.get("/tenants")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "api_key" not in data[0]


@pytest.mark.asyncio
async def test_get_tenant(client: AsyncClient) -> None:
    create_response = await client.post("/tenants", json={"name": "Test Tenant"})
    tenant_data = create_response.json()
    tenant_id = tenant_data["id"]
    client.headers.update({"X-Tenant-ID": tenant_id, "X-API-KEY": tenant_data["api_key"]})

    response = await client.get(f"/tenants/{tenant_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tenant_id
    assert "api_key" not in data


@pytest.mark.asyncio
async def test_delete_tenant(client: AsyncClient) -> None:
    create_response = await client.post("/tenants", json={"name": "Test Tenant"})
    tenant_data = create_response.json()
    tenant_id = tenant_data["id"]
    client.headers.update({"X-Tenant-ID": tenant_id, "X-API-KEY": tenant_data["api_key"]})

    response = await client.delete(f"/tenants/{tenant_id}")

    assert response.status_code == 204
