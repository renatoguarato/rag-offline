from __future__ import annotations

from contextvars import ContextVar

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TenantContext:
    def __init__(self, tenant_id: str, api_key: str) -> None:
        self.tenant_id = tenant_id
        self.api_key = api_key


_tenant_context: ContextVar[TenantContext | None] = ContextVar("tenant_context", default=None)


def get_tenant_context() -> TenantContext:
    context = _tenant_context.get()
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No tenant context found",
        )
    return context


def set_tenant_context(tenant_id: str, api_key: str) -> None:
    _tenant_context.set(TenantContext(tenant_id, api_key))


def clear_tenant_context() -> None:
    _tenant_context.set(None)


class TenantAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.tenant_id_header = settings.TENANT_ID_HEADER
        self.api_key_header = settings.API_KEY_HEADER

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        method = request.method

        if path in ["/", "/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        if path == "/tenants" and method == "POST":
            return await call_next(request)

        tenant_id = request.headers.get(self.tenant_id_header)
        api_key = request.headers.get(self.api_key_header)

        if not tenant_id:
            logger.warning(f"Missing {self.tenant_id_header} header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Missing {self.tenant_id_header} header",
            )

        if not api_key:
            logger.warning(f"Missing {self.api_key_header} header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Missing {self.api_key_header} header",
            )

        set_tenant_context(tenant_id, api_key)

        try:
            response = await call_next(request)
            return response
        finally:
            clear_tenant_context()
