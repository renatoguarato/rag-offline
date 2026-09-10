from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.rag import router as rag_router
from app.api.tenants import router as tenants_router
from app.core.config import settings
from app.core.database import init_db
from app.core.error_handlers import generic_exception_handler, validation_exception_handler
from app.core.logging import setup_logging
from app.middleware.tenant_auth import TenantAuthMiddleware

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield
    pass


app = FastAPI(
    title="RAG Offline Multi-Tenant API",
    description="Production-ready offline RAG application with multi-tenant support",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TenantAuthMiddleware)

app.include_router(health_router)
app.include_router(tenants_router)
app.include_router(documents_router)
app.include_router(rag_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "RAG Offline Multi-Tenant API",
        "version": "1.0.0",
        "status": "running",
    }
