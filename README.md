# RAG Offline Multi-Tenant Application

Production-ready offline RAG (Retrieval-Augmented Generation) application with secure multi-tenant isolation.

## Features

- **Multi-tenant Architecture**: Complete tenant isolation with UUID-based tenant IDs
- **Secure Authentication**: API key-based authentication for each tenant
- **Document Processing**: Support for PDF, DOCX, and TXT files
- **Vector Storage**: ChromaDB for efficient vector similarity search
- **LLM Integration**: Ollama (llama3) for embeddings and text generation
- **Async Operations**: Fully async Python 3.11 with FastAPI
- **RESTful API**: Clean, well-documented API endpoints
- **Production-Ready**: Comprehensive error handling, logging, and testing

## Stack

- Python 3.11
- FastAPI
- Ollama (llama3)
- ChromaDB
- SQLite (with SQLAlchemy)
- Pytest

## Prerequisites

- Python 3.11 or higher
- Ollama running locally with llama3 model installed
  ```bash
  ollama pull llama3
  ollama pull nomic-embed-text
  ollama serve
  ```

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd rag-offline

# Install Python 3.11 and project dependencies
uv sync
```

For a reproducible installation using the committed lockfile, run `uv sync --locked`.

## Configuration

Copy the example environment file and configure as needed:

```bash
cp .env.example .env
```

Available configuration options:
- `DATABASE_URL`: SQLite database connection string
- `OLLAMA_BASE_URL`: Ollama API endpoint (default: http://localhost:11434)
- `OLLAMA_MODEL`: Ollama model to use (default: llama3)
- `OLLAMA_EMBEDDING_MODEL`: Ollama embedding model (default: nomic-embed-text)
- `CHROMA_PERSIST_DIRECTORY`: ChromaDB storage location
- `RAG_MAX_DISTANCE`: optional maximum Chroma distance; unset disables filtering
- `MAX_DOCUMENT_SIZE`: Maximum document upload size in bytes

## Running the Application

```bash
# Development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

For a database with existing data, apply schema migrations before starting:

```bash
uv run alembic upgrade head
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## API Usage

### Health Check

```bash
curl http://localhost:8000/health
```

### Create Tenant

```bash
curl -X POST http://localhost:8000/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "My Organization"}'
```

Response includes tenant ID and API key for authentication.

### Upload Document

```bash
curl -X POST http://localhost:8000/documents \
  -H "X-Tenant-ID: <tenant-id>" \
  -H "X-API-KEY: <api-key>" \
  -F "file=@document.pdf"
```

### Query Documents (RAG)

```bash
curl -X POST http://localhost:8000/rag/query \
  -H "X-Tenant-ID: <tenant-id>" \
  -H "X-API-KEY: <api-key>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?", "n_results": 5}'
```

### List Documents

```bash
curl http://localhost:8000/documents \
  -H "X-Tenant-ID: <tenant-id>" \
  -H "X-API-KEY: <api-key>"
```

## Security

All API endpoints (except `/health`, `/docs`, `/redoc`, `/openapi.json`) require:
- `X-Tenant-ID`: UUID of the tenant
- `X-API-KEY`: API key for the tenant

Multi-tenant isolation ensures:
- Separate ChromaDB collections per tenant
- Tenant-specific document storage
- API key validation for all requests
- No cross-tenant data access

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run single test file
uv run pytest tests/test_tenants.py

# Run single test
uv run pytest tests/test_tenants.py::test_create_tenant
```

## Code Quality

```bash
# Type checking
uv run pyright

# Linting
uv run ruff check .

# Formatting
uv run ruff format .
```

## Architecture

The application follows a strict hexagonal architecture (ports and adapters):

- `app/domain/`: entities and business rules with no framework or infrastructure dependency.
- `app/application/`: typed use cases and secondary ports; it depends only on the domain.
- `app/adapters/inbound/http/`: FastAPI routes, schemas, authentication and presenters.
- `app/adapters/outbound/`: integrations with SQLAlchemy, ChromaDB, Ollama and files.
- `app/bootstrap/`: composition root, configuration, lifecycle and concrete dependency wiring.

Use cases receive ports through constructors. ORM models never cross the persistence adapter, and architectural tests reject imports that violate the dependency direction.

## Project Structure

```
rag-offline/
├── app/
│   ├── adapters/      # Inbound HTTP and outbound integrations
│   ├── application/   # Use cases and ports
│   ├── bootstrap/     # Composition root and runtime configuration
│   └── domain/        # Framework-independent business concepts
├── alembic/           # Database migrations
├── tests/             # Test suite
└── chroma_db/         # Vector storage
```

## License

Proprietary
