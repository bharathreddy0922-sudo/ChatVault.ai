# Source-Grounded Research Copilot API

FastAPI backend for the Source-Grounded Research Copilot application.

## Features

- **Document Processing**: Parse PDFs, DOCX, TXT, CSV, XLSX files with OCR support
- **Web Crawling**: Crawl URLs with configurable depth using Playwright
- **Vector Search**: Local embeddings with Qdrant/FAISS
- **RAG Pipeline**: Source-grounded responses with citations
- **Background Processing**: Celery + Redis for document ingestion
- **Local LLM**: Ollama integration with streaming

## Prerequisites

1. **Python 3.9+** with [uv](https://docs.astral.sh/uv/)
2. **Qdrant** (local installation)
3. **Redis** (local installation)
4. **Ollama** with mistral model

## Installation

### 1. Install Dependencies (macOS)

```bash
# Install Qdrant and Redis
brew install qdrant redis
brew services start qdrant
brew services start redis

# Install Ollama
brew install ollama
ollama pull mistral
```

### 2. Setup Python Environment

```bash
# Create virtual environment
uv venv

# Install dependencies
uv pip install -e .

# Install Playwright browsers
uv run playwright install
```

### 3. Environment Configuration

Create a `.env` file in the `apps/api` directory:

```env
# Database
DATABASE_URL=sqlite:///./quanta_copilot.db

# Redis
REDIS_URL=redis://localhost:6379

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# File upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=52428800
ALLOWED_EXTENSIONS=[".pdf", ".docx", ".txt", ".csv", ".xlsx"]

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=150

# RAG
TOP_K=8
SIMILARITY_THRESHOLD=0.7

# Web crawling
MAX_CRAWL_DEPTH=2
MAX_URLS_PER_CRAWL=50

# Security
SECRET_KEY=your-secret-key-change-in-production
```

## Running the Application

### 1. Start the API Server

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

### 2. Start Celery Worker (in another terminal)

```bash
celery -A src.workers.celery_app.celery worker --loglevel=INFO
```

### 3. Start Celery Monitor (optional)

```bash
celery -A src.workers.celery_app.celery flower
```

## API Endpoints

### Bots
- `POST /bots` - Create a new bot
- `GET /bots` - List all bots
- `GET /bots/{id}` - Get a specific bot
- `GET /bots/slug/{slug}` - Get a bot by slug
- `DELETE /bots/{id}` - Delete a bot

### Documents
- `POST /bots/{id}/add-docs` - Upload documents
- `GET /bots/{id}/documents` - List documents
- `DELETE /bots/{id}/documents/{doc_id}` - Delete a document

### URLs
- `POST /bots/{id}/add-urls` - Add URLs for crawling
- `GET /bots/{id}/urls` - List URL sources
- `DELETE /bots/{id}/urls/{url_id}` - Delete a URL source

### Chat
- `POST /chat/{slug}` - Chat with a bot (RAG)
- `GET /chat/{slug}/history` - Get chat history
- `GET /chat/{slug}/chats` - List chats
- `DELETE /chat/{slug}/chats/{chat_id}` - Delete a chat

### Status
- `GET /bots/{id}/status` - Get bot processing status
- `GET /task/{task_id}` - Get task status
- `GET /bots/{id}/documents/status` - Get documents status
- `GET /bots/{id}/urls/status` - Get URLs status

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development

### Code Structure

```
src/
├── main.py              # FastAPI application
├── config.py            # Configuration settings
├── deps.py              # Dependencies (database, etc.)
├── models.py            # SQLModel data models
├── routes/              # API routes
│   ├── bots.py         # Bot management
│   ├── uploads.py      # Document uploads
│   ├── ingest.py       # URL crawling
│   ├── chat.py         # RAG chat
│   └── status.py       # Status endpoints
├── services/            # Business logic
│   ├── parsing.py      # Document parsing
│   ├── chunking.py     # Text chunking
│   ├── embed.py        # Embeddings
│   ├── index.py        # Vector database
│   ├── rag.py          # RAG pipeline
│   └── crawl.py        # Web crawling
└── workers/             # Background tasks
    ├── celery_app.py   # Celery configuration
    └── tasks.py        # Celery tasks
```

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black src/
uv run isort src/
```

## Troubleshooting

### Qdrant Connection Issues
If Qdrant is not available, the system will automatically fall back to FAISS (in-memory).

### OCR Issues
If PaddleOCR fails to install, the system will work without OCR support for image-based PDFs.

### Memory Issues
For large documents, consider:
- Reducing `CHUNK_SIZE` in config
- Increasing system memory
- Using smaller embedding models

### Performance
- Use SSD storage for better I/O performance
- Ensure sufficient RAM for embedding models
- Consider using GPU for embeddings if available
