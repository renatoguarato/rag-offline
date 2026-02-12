from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_create_tenant(client):
    response = await client.post("/tenants", json={"name": "Test Tenant"})

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Tenant"
    assert "api_key" in data
    assert len(data["api_key"]) == 64


@pytest.mark.asyncio
async def test_list_tenants(client):
    await client.post("/tenants", json={"name": "Tenant 1"})
    await client.post("/tenants", json={"name": "Tenant 2"})

    response = await client.get("/tenants")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_tenant(client):
    create_response = await client.post("/tenants", json={"name": "Test Tenant"})
    tenant_id = create_response.json()["id"]

    response = await client.get(f"/tenants/{tenant_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tenant_id


@pytest.mark.asyncio
async def test_delete_tenant(client):
    create_response = await client.post("/tenants", json={"name": "Test Tenant"})
    tenant_id = create_response.json()["id"]

    response = await client.delete(f"/tenants/{tenant_id}")

    assert response.status_code == 204
