import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./quanta_copilot.db"
    
    # Optional external services (with fallbacks)
    redis_url: Optional[str] = None  # None = use in-process tasks
    qdrant_url: Optional[str] = None  # None = use FAISS
    qdrant_api_key: Optional[str] = None
    
    # Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "mistral:7b-instruct-q4_K_M"  # M1-optimized model
    
    # File upload (M1-optimized limits)
    upload_dir: str = "./uploads"
    max_file_size: int = 30 * 1024 * 1024  # 30MB for 8GB RAM
    max_pages_per_document: int = 100  # Limit for large PDFs
    allowed_extensions: list = [".pdf", ".docx", ".txt", ".csv", ".xlsx"]
    
    # Embeddings (M1-optimized)
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 800  # Smaller chunks for memory efficiency
    chunk_overlap: int = 150
    
    # RAG (M1-optimized)
    top_k: int = 8
    similarity_threshold: float = 0.7
    max_concurrent_tasks: int = 2  # Limit concurrent processing
    
    # Web crawling (lightweight)
    max_crawl_depth: int = 1  # Default depth 1
    max_urls_per_crawl: int = 20  # Reduced for memory
    crawl_timeout: int = 30  # Timeout in seconds
    
    # OCR (optional)
    enable_ocr: bool = False  # Disabled by default for M1
    ocr_language: str = "eng"
    
    # Playwright (optional)
    enable_playwright: bool = False  # Disabled by default
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"


settings = Settings()
