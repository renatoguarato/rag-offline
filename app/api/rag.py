from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import authenticated_tenant, get_query_use_case
from app.application.ports import TenantRecord
from app.application.use_cases import QueryRAG
from app.schemas.common import QueryRequest, QueryResponse

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    tenant: TenantRecord = Depends(authenticated_tenant),
    use_case: QueryRAG = Depends(get_query_use_case),
) -> QueryResponse:
    result = await use_case.execute(tenant.id, request.question, request.n_results)

    return QueryResponse(
        answer=result.answer,
        sources=[dict(source) for source in result.sources],
        context_chunks=result.context_chunks,
    )
