# Agent Guidelines - RAG Offline Multi-Tenant Application

## Project Overview
Production-ready offline RAG application using Python 3.11, FastAPI, Ollama (llama3), ChromaDB, and SQLite with secure multi-tenant isolation.

## Build & Test Commands

### Setup
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Linting & Formatting
```bash
# Type checking
pyright

# Linting
ruff check .

# Formatting
ruff format .
```

### Testing
```bash
# Run all tests
pytest

# Run single test file
pytest tests/test_module.py

# Run single test
pytest tests/test_module.py::test_function

# Run with coverage
pytest --cov=app --cov-report=html
```

## Code Style Guidelines

### Imports
- Order: stdlib, third-party, local
- Group imports with blank lines between groups
- Use `from x import y` for modules, not `import x.y as y`
- Ban star imports (`from x import *`)
- Use `__all__` in modules to define public API

### Type Hints
- Always annotate function signatures with types
- Use `typing` module (e.g., `Optional[str]`, `List[int]`, `Dict[str, Any]`)
- Use `pydantic` for request/response models
- Use `from __future__ import annotations` for forward references
- Return `None` explicitly when applicable

### Naming Conventions
- Classes: `PascalCase` (e.g., `TenantService`, `RAGEngine`)
- Functions/methods: `snake_case` (e.g., `create_tenant`, `get_document`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_DOCUMENT_SIZE`, `API_KEY_HEADER`)
- Private members: `_snake_case` (e.g., `_internal_method`, `_cache`)
- Modules/files: `snake_case` (e.g., `tenant_service.py`, `rag_engine.py`)

### Error Handling
- Use custom exceptions inheriting from `Exception`
- Wrap third-party library exceptions in application-specific ones
- Never expose sensitive data in error messages (API keys, tenant internals)
- Log errors with context using structured logging
- Return HTTP status codes: 400 for client errors, 500 for server errors
- Use FastAPI's `HTTPException` for HTTP responses

### API Design
- RESTful endpoints with clear resource naming
- Use HTTP verbs correctly (GET/POST/PUT/PATCH/DELETE)
- Return consistent response structure: `{"data": ..., "error": ...}`
- Validate all inputs using Pydantic models
- Use query parameters for filtering, path parameters for identification
- Document all endpoints with OpenAPI/Swagger comments

### Security (CRITICAL)
- Always validate `X-Tenant-ID` and `X-API-KEY` headers
- Never expose tenant data across boundaries
- Use UUIDs for all tenant IDs
- Sanitize all user inputs before database/LLM queries
- Implement rate limiting and request size limits
- Log all security-relevant events (auth failures, access attempts)
- Never log API keys or sensitive tokens
- Use parameterized queries for all database operations
- Validate file types and sizes for document uploads

### Database
- Use SQLAlchemy with async sessions
- Migrations with Alembic
- Foreign keys for all relationships
- Indexes on frequently queried fields (tenant_id, created_at)
- Soft deletes with `deleted_at` timestamp
- Transaction management for multi-step operations

### Testing
- Use pytest with async support
- Mock external services (Ollama, ChromaDB)
- Test both success and failure paths
- Test multi-tenant isolation explicitly
- Integration tests for API endpoints
- Unit tests for business logic
- Use fixtures for common test data

### Documentation
- Docstrings for all public functions/classes (Google style)
- Type hints in docstrings when complex
- README with setup and usage instructions
- API documentation via FastAPI's auto-generated Swagger UI
- Document security model and threat assumptions

### Performance
- Use async/await for I/O operations
- Connection pooling for database and external services
- Caching for expensive operations (RAG results)
- Pagination for large result sets
- Background tasks for long-running operations
- Monitor and log slow operations

## OpenCode Rules (from spec)
- Create everything automatically - don't wait for permission
- Don't simplify security features
- Never remove or weaken security measures
- Production-ready implementation required
