from __future__ import annotations

import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_document(tenant_client: AsyncClient) -> None:
    file_content = b"Test document content for testing purposes."

    files = {
        "file": ("test.txt", io.BytesIO(file_content), "text/plain"),
    }

    response = await tenant_client.post("/documents", files=files)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "test.txt"
    assert data["content_type"] == "text/plain"
    assert data["file_size"] == len(file_content)
    assert data["index_status"] == "indexed"


@pytest.mark.asyncio
async def test_list_documents(tenant_client: AsyncClient) -> None:
    file_content = b"Test document content."

    files = {
        "file": ("test.txt", io.BytesIO(file_content), "text/plain"),
    }

    await tenant_client.post("/documents", files=files)

    response = await tenant_client.get("/documents")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_document(tenant_client: AsyncClient) -> None:
    file_content = b"Test document content."

    files = {
        "file": ("test.txt", io.BytesIO(file_content), "text/plain"),
    }

    upload_response = await tenant_client.post("/documents", files=files)
    document_id = upload_response.json()["id"]

    response = await tenant_client.get(f"/documents/{document_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document_id


@pytest.mark.asyncio
async def test_delete_document(tenant_client: AsyncClient) -> None:
    file_content = b"Test document content."

    files = {
        "file": ("test.txt", io.BytesIO(file_content), "text/plain"),
    }

    upload_response = await tenant_client.post("/documents", files=files)
    document_id = upload_response.json()["id"]

    response = await tenant_client.delete(f"/documents/{document_id}")

    assert response.status_code == 204
