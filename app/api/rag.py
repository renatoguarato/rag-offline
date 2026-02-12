from __future__ import annotations

from fastapi import APIRouter, Depends

from app.middleware.tenant_auth import get_tenant_context
from app.schemas.common import QueryRequest, QueryResponse
from app.services.rag_engine import rag_engine

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
) -> QueryResponse:
    context = get_tenant_context()

    result = await rag_engine.query(
        tenant_id=context.tenant_id,
        question=request.question,
        n_results=request.n_results,
    )

    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        context_chunks=result["context_chunks"],
    )
