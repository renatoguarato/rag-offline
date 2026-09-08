from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends

from app.api.dependencies import get_ollama_provider
from app.application.ports import EmbeddingProvider
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(provider: EmbeddingProvider = Depends(get_ollama_provider)) -> HealthResponse:
    ollama_connected = await provider.is_available()

    return HealthResponse(
        status="healthy" if ollama_connected else "degraded",
        ollama_connected=ollama_connected,
        timestamp=datetime.utcnow(),
    )
