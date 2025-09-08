import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import logging
from ..config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.model_name = settings.embedding_model
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string"""
        try:
            if not self.model:
                raise ValueError("Embedding model not loaded")
            
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple text strings"""
        try:
            if not self.model:
                raise ValueError("Embedding model not loaded")
            
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error embedding texts: {e}")
            raise
    
    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Embed a list of chunks and return chunks with embeddings"""
        try:
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embed_texts(texts)
            
            # Add embeddings to chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk['embedding'] = embedding
            
            return chunks
        except Exception as e:
            logger.error(f"Error embedding chunks: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors"""
        try:
            if not self.model:
                raise ValueError("Embedding model not loaded")
            
            # Create a dummy embedding to get the dimension
            dummy_embedding = self.model.encode("test", convert_to_tensor=False)
            return dummy_embedding.shape[0]
        except Exception as e:
            logger.error(f"Error getting embedding dimension: {e}")
            raise
