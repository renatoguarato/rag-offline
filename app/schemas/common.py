from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class TenantResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TenantCreatedResponse(TenantResponse):
    api_key: str


class DocumentCreate(BaseModel):
    pass


class DocumentResponse(BaseModel):
    id: str
    tenant_id: str
    filename: str
    content_type: str
    file_size: int
    chunk_count: int
    index_status: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    n_results: int = Field(default=5, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Question must not be blank")
        return normalized


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict[str, object]]
    context_chunks: int


class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    timestamp: datetime


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
