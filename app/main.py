from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.rag import router as rag_router
from app.api.tenants import router as tenants_router
from app.core.config import settings
from app.core.database import init_db
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
async def root() -> dict:
    return {
        "name": "RAG Offline Multi-Tenant API",
        "version": "1.0.0",
        "status": "running",
    }
