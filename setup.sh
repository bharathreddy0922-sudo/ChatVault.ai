#!/bin/bash

echo "🚀 Setting up Source-Grounded Research Copilot"
echo "=============================================="

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed. Please install it first:"
    echo "   https://brew.sh/"
    exit 1
fi

echo "📦 Installing system dependencies (M1-optimized)..."

# Install optional dependencies (lightweight setup)
echo "Installing optional dependencies..."

# Install Qdrant (optional)
if command -v qdrant &> /dev/null; then
    echo "Qdrant already installed"
else
    echo "Installing Qdrant (optional)..."
    brew install qdrant
fi

# Install Redis (optional, for future use)
if command -v redis-server &> /dev/null; then
    echo "Redis already installed"
else
    echo "Installing Redis (optional)..."
    brew install redis
fi

# Install Ollama
if command -v ollama &> /dev/null; then
    echo "Ollama already installed"
else
    echo "Installing Ollama..."
    brew install ollama
fi

# Install Tesseract (optional, for OCR)
if command -v tesseract &> /dev/null; then
    echo "Tesseract already installed"
else
    echo "Installing Tesseract (optional, for OCR)..."
    brew install tesseract
fi

# Start services (optional)
echo "🚀 Starting optional services..."
brew services start qdrant 2>/dev/null || echo "Qdrant not started (optional)"
brew services start redis 2>/dev/null || echo "Redis not started (optional)"

# Pull Ollama model (M1-optimized)
echo "📥 Pulling Ollama model (M1-optimized)..."
ollama pull mistral:7b-instruct-q4_K_M

echo ""
echo "✅ System dependencies installed!"
echo ""
echo "🔧 Next steps (M1-optimized):"
echo "1. Copy env.example to .env in apps/api/"
echo "2. Install Python dependencies: cd apps/api && uv venv && uv pip install -e ."
echo "3. Install optional dependencies: uv pip install -e '.[ocr,playwright,qdrant]' (if needed)"
echo "4. Install Node.js dependencies: cd apps/web && npm install"
echo "5. Start the backend: cd apps/api && uv run uvicorn src.main:app --reload"
echo "6. Start the frontend: cd apps/web && npm run dev"
echo ""
echo "💡 M1 Optimization Notes:"
echo "- FAISS is used as primary vector database (no external dependencies)"
echo "- In-process tasks (no Celery/Redis required)"
echo "- Optional OCR and Playwright (disabled by default)"
echo "- 30MB file size limit, 100 page limit for PDFs"
echo "- 8GB RAM optimized with concurrent task limits"
echo ""
echo "🌐 The application will be available at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
