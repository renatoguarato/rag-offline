from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from app.schemas.common import HealthResponse
from app.services.ollama_service import ollama_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    ollama_connected = await ollama_service.check_connection()

    return HealthResponse(
        status="healthy" if ollama_connected else "degraded",
        ollama_connected=ollama_connected,
        timestamp=datetime.utcnow(),
    )
