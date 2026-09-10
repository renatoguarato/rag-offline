from __future__ import annotations

from typing import Any

from fastapi import Request

from app.adapters.inbound.http.auth import credentials
from app.application.use_cases import DocumentUseCases, HealthCheck, QueryRAG, TenantUseCases
from app.domain.entities import Tenant


def _runtime(request: Request) -> Any:
    return request.app.state.runtime


def tenant_use_cases(request: Request) -> TenantUseCases:
    return _runtime(request).tenant_use_cases


def document_use_cases(request: Request) -> DocumentUseCases:
    return _runtime(request).document_use_cases


def query_use_case(request: Request) -> QueryRAG:
    return _runtime(request).query_rag


def health_check(request: Request) -> HealthCheck:
    return _runtime(request).health_check


async def authenticated_tenant(request: Request) -> Tenant:
    value = credentials()
    return await _runtime(request).authenticator.execute(value.tenant_id, value.api_key)
