from __future__ import annotations

from contextvars import ContextVar
from uuid import UUID

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp

from app.bootstrap.config import Settings


class TenantCredentials:
    def __init__(self, tenant_id: str, api_key: str) -> None:
        self.tenant_id = tenant_id
        self.api_key = api_key


_credentials: ContextVar[TenantCredentials | None] = ContextVar("tenant_credentials", default=None)


def credentials() -> TenantCredentials:
    value = _credentials.get()
    if value is None:
        raise ValueError("Tenant credentials are not available")
    return value


class TenantAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self._tenant_header = settings.TENANT_ID_HEADER
        self._api_key_header = settings.API_KEY_HEADER

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in {"/", "/health", "/docs", "/openapi.json", "/redoc"}:
            return await call_next(request)
        if request.url.path == "/tenants" and request.method == "POST":
            return await call_next(request)
        tenant_id = request.headers.get(self._tenant_header)
        api_key = request.headers.get(self._api_key_header)
        if not tenant_id or not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Unauthorized", "detail": "Missing tenant credentials"},
            )
        try:
            UUID(tenant_id)
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Unauthorized", "detail": "Invalid tenant credentials"},
            )
        token = _credentials.set(TenantCredentials(tenant_id, api_key))
        try:
            return await call_next(request)
        finally:
            _credentials.reset(token)
