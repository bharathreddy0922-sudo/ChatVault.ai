from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .deps import create_db_and_tables
from .routes import bots, uploads, chat, ingest, status
from .config import settings

# Create FastAPI app
app = FastAPI(
    title="Source-Grounded Research Copilot API",
    description="A RAG-powered research assistant with source citations",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(bots.router)
app.include_router(uploads.router)
app.include_router(chat.router)
app.include_router(ingest.router)
app.include_router(status.router)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_db_and_tables()

@app.get("/")
async def root():
    return {
        "message": "Source-Grounded Research Copilot API (M1 Optimized)",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0", "optimized": "M1"}
