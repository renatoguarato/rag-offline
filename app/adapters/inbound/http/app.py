from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.adapters.inbound.http.auth import TenantAuthMiddleware
from app.adapters.inbound.http.routes import build_router
from app.application.use_cases import (
    ApplicationError,
    DocumentNotFound,
    DocumentProcessingFailed,
    InvalidTenantCredentials,
)
from app.bootstrap.config import Settings
from app.bootstrap.runtime import Runtime


def create_app(runtime: Runtime, settings: Settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        yield
        await runtime.close()

    app = FastAPI(
        title="RAG Offline Multi-Tenant API",
        description="Production-ready offline RAG application with multi-tenant support",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.runtime = runtime
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(ApplicationError, _application_handler)
    app.add_exception_handler(Exception, _generic_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TenantAuthMiddleware, settings=settings)
    app.include_router(build_router(settings))
    return app


async def _validation_handler(_: Request, exc: Exception) -> JSONResponse:
    error = cast(RequestValidationError, exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation error", "detail": error.errors()},
    )


async def _application_handler(_: Request, exc: Exception) -> JSONResponse:
    error = cast(ApplicationError, exc)
    if isinstance(error, InvalidTenantCredentials):
        code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(error, DocumentNotFound):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(error, DocumentProcessingFailed):
        code = status.HTTP_400_BAD_REQUEST
    else:
        code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return JSONResponse(
        status_code=code, content={"error": error.__class__.__name__, "detail": str(error)}
    )


async def _generic_handler(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
