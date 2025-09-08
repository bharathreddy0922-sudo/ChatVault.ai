# Source-Grounded Research Copilot (M1 Optimized)

A lightweight web app optimized for MacBook M1 with 8GB RAM that lets users upload multiple documents & URLs, then chat with them using source-grounded responses with citations. Features graceful fallbacks and resource-efficient processing.

## 🚀 Quick Start

### Option 1: Automated Setup (macOS)

```bash
# Run the setup script
./setup.sh
```

### Option 2: Manual Setup

#### Prerequisites

1. **Python 3.9+** with [uv](https://docs.astral.sh/uv/)
2. **Node.js 18+**
3. **Homebrew** (for macOS dependencies)

#### 1. Install System Dependencies (M1 Optimized)

```bash
# Install optional dependencies (lightweight setup)
brew install ollama  # Required
brew install qdrant  # Optional (FAISS fallback available)
brew install redis   # Optional (in-process tasks available)
brew install tesseract  # Optional (for OCR)

# Start optional services
brew services start qdrant  # Optional
brew services start redis   # Optional

# Pull M1-optimized Ollama model
ollama pull mistral:7b-instruct-q4_K_M
```

#### 2. Backend Setup

```bash
cd apps/api

# Create virtual environment and install dependencies
uv venv
uv pip install -e .

# Install optional dependencies (if needed)
uv pip install -e '.[ocr,playwright,qdrant]'  # Optional

# Copy environment file
cp env.example .env

# Start the API server
uv run uvicorn src.main:app --reload
```

# No additional terminal needed - uses in-process tasks!

#### 3. Frontend Setup

```bash
cd apps/web

# Install dependencies
npm install

# Start development server
npm run dev
```

### Usage

1. Open http://localhost:3000
2. Create a new bot
3. Upload documents or add URLs
4. Chat with your documents using source-grounded responses

## ✨ Features

- **Source-Grounded Responses**: Only answer from retrieved chunks with inline citations [1][2]
- **Multi-Document Support**: Upload PDFs, DOCX, TXT, CSV, XLSX files
- **Lightweight Web Crawling**: Requests + Trafilatura (Playwright optional)
- **Smart Chunking**: Semantic text splitting with heading awareness
- **FAISS Vector Search**: In-process similarity search (Qdrant optional)
- **Local LLM**: Ollama integration with streaming responses
- **In-Process Tasks**: No external task queues required
- **Modern UI**: Clean, responsive interface with Material-UI

## 🎯 M1 Optimizations

- **FAISS-First Vector Database**: In-process, zero-overhead vector search
- **Lightweight Dependencies**: Optional Qdrant, Redis, OCR, and Playwright
- **Memory-Efficient**: 30MB file limits, 100-page PDF limits, concurrent task limits
- **Graceful Fallbacks**: Automatic fallback to lighter alternatives
- **Resource Guards**: Timeouts, size limits, and concurrent task limits

## 🏗️ Architecture

### Tech Stack (M1 Optimized)

- **Frontend**: Next.js (App Router), MUI, React Query, SSE streaming
- **Backend**: FastAPI, Pydantic, Uvicorn
- **Document Parsing**: PyMuPDF, python-docx, pandas (pytesseract optional)
- **Web Crawling**: Requests + Trafilatura (Playwright optional)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector DB**: FAISS (primary) with Qdrant (optional)
- **LLM**: Ollama with mistral:7b-instruct-q4_K_M
- **Background Jobs**: In-process async tasks (Celery optional)
- **Database**: SQLite with SQLModel

### Project Structure

```
quanta-copilot/
├── apps/
│   ├── web/                 # Next.js frontend
│   │   ├── app/            # App Router pages
│   │   ├── components/     # React components
│   │   └── lib/           # Utilities and API client
│   └── api/                # FastAPI backend
│       ├── src/
│       │   ├── routes/     # API endpoints
│       │   ├── services/   # Business logic
│       │   └── workers/    # Background tasks
│       └── pyproject.toml  # Python dependencies
├── setup.sh               # Automated setup script
└── README.md
```

## 📚 API Endpoints

### Bots
- `POST /bots` - Create a new bot
- `GET /bots` - List all bots
- `GET /bots/{id}` - Get a specific bot
- `DELETE /bots/{id}` - Delete a bot

### Documents
- `POST /bots/{id}/add-docs` - Upload documents
- `GET /bots/{id}/documents` - List documents
- `DELETE /bots/{id}/documents/{doc_id}` - Delete a document

### URLs
- `POST /bots/{id}/add-urls` - Add URLs for crawling
- `GET /bots/{id}/urls` - List URL sources

### Chat
- `POST /chat/{slug}` - Chat with a bot (RAG)
- `GET /chat/{slug}/history` - Get chat history

### Status
- `GET /bots/{id}/status` - Get processing status
- `GET /task/{task_id}` - Get task status

## 🔧 Development

### Backend Development

```bash
cd apps/api

# Run tests
uv run pytest

# Format code
uv run black src/
uv run isort src/

# API documentation
# Visit http://localhost:8000/docs
```

### Frontend Development

```bash
cd apps/web

# Run linting
npm run lint

# Build for production
npm run build
```

## 🚀 Deployment

### Production Setup

1. **Environment Variables**: Configure production environment variables
2. **Database**: Use PostgreSQL instead of SQLite for production
3. **Vector Database**: Use managed Qdrant or Pinecone
4. **LLM**: Use OpenAI, Anthropic, or other cloud providers
5. **File Storage**: Use S3 or similar for file storage

### Docker Deployment

```dockerfile
# Backend
FROM python:3.9-slim
WORKDIR /app
COPY apps/api/ .
RUN pip install -e .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend
FROM node:18-alpine
WORKDIR /app
COPY apps/web/ .
RUN npm install && npm run build
CMD ["npm", "start"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **Qdrant Connection**: If Qdrant is unavailable, the system automatically uses FAISS
2. **OCR Issues**: pytesseract is optional and disabled by default
3. **Memory Issues**: System is optimized for 8GB RAM with built-in limits
4. **File Upload**: 30MB limit, 100-page PDF limit for memory efficiency
5. **Playwright**: Optional for JavaScript rendering, falls back to requests

### Getting Help

- Check the individual README files in `apps/web/` and `apps/api/`
- Review the API documentation at http://localhost:8000/docs
- Open an issue on GitHub for bugs or feature requests