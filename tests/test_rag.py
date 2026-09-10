from __future__ import annotations

import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_query_rag(tenant_client: AsyncClient) -> None:
    file_content = b"""
    Python is a high-level, interpreted programming language.
    It was created by Guido van Rossum and first released in 1991.
    Python emphasizes code readability with its notable use of significant whitespace.
    """

    files = {
        "file": ("python.txt", io.BytesIO(file_content), "text/plain"),
    }

    await tenant_client.post("/documents", files=files)

    response = await tenant_client.post(
        "/rag/query",
        json={"question": "Who created Python?", "n_results": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "context_chunks" in data
    assert data["context_chunks"] > 0


@pytest.mark.asyncio
async def test_query_rag_no_documents(tenant_client: AsyncClient) -> None:
    response = await tenant_client.post(
        "/rag/query",
        json={"question": "What is Python?", "n_results": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
