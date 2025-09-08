import logging
import numpy as np
from typing import List, Dict, Any, Optional
import faiss
import pickle
import os
from pathlib import Path
from ..config import settings

logger = logging.getLogger(__name__)


class FAISSIndex:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.index = None
        self.metadata = []
        self.index_path = f"./indices/{collection_name}.faiss"
        self.metadata_path = f"./indices/{collection_name}_metadata.pkl"
        self._ensure_index_dir()
        self._load_or_create_index()
    
    def _ensure_index_dir(self):
        """Ensure the indices directory exists"""
        Path("./indices").mkdir(exist_ok=True)
    
    def _load_or_create_index(self):
        """Load existing index or create a new one"""
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
                # Load existing index
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                logger.info(f"Loaded existing FAISS index: {self.collection_name}")
            else:
                # Create new index
                self._create_new_index()
        except Exception as e:
            logger.warning(f"Error loading index, creating new one: {e}")
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        # Use IndexFlatIP for cosine similarity (after normalization)
        # Start with dimension 384 (all-MiniLM-L6-v2)
        self.index = faiss.IndexFlatIP(384)
        self.metadata = []
        logger.info(f"Created new FAISS index: {self.collection_name}")
    
    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Add chunks to the index"""
        try:
            if not chunks:
                return
            
            # Extract embeddings
            embeddings = np.array([chunk['embedding'] for chunk in chunks])
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to index
            self.index.add(embeddings)
            
            # Store metadata
            for chunk in chunks:
                self.metadata.append({
                    'chunk_id': chunk['chunk_id'],
                    'text': chunk['text'],
                    'document_id': chunk.get('document_id'),
                    'location': chunk['location'],
                    'headings': chunk.get('headings', [])
                })
            
            # Save index and metadata
            self._save_index()
            
            logger.info(f"Added {len(chunks)} chunks to FAISS index: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error adding chunks to FAISS index: {e}")
            raise
    
    def search(self, query_embedding: List[float], top_k: int = 8, 
               filter_document_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        try:
            if self.index.ntotal == 0:
                return []
            
            # Normalize query embedding
            query_vector = np.array([query_embedding])
            faiss.normalize_L2(query_vector)
            
            # Search
            scores, indices = self.index.search(query_vector, min(top_k * 2, self.index.ntotal))
            
            results = []
            seen_docs = set()
            
            for score, idx in zip(scores[0], indices[0]):
                if idx >= len(self.metadata):
                    continue
                
                metadata = self.metadata[idx]
                
                # Apply document filter if specified
                if filter_document_ids and metadata['document_id'] not in filter_document_ids:
                    continue
                
                # Deduplicate by document (keep only first occurrence)
                if metadata['document_id'] in seen_docs:
                    continue
                
                seen_docs.add(metadata['document_id'])
                
                results.append({
                    'chunk_id': metadata['chunk_id'],
                    'score': float(score),
                    'text': metadata['text'],
                    'document_id': metadata['document_id'],
                    'location': metadata['location'],
                    'headings': metadata['headings']
                })
                
                if len(results) >= top_k:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching FAISS index: {e}")
            return []
    
    def delete_collection(self):
        """Delete the collection"""
        try:
            if os.path.exists(self.index_path):
                os.remove(self.index_path)
            if os.path.exists(self.metadata_path):
                os.remove(self.metadata_path)
            
            self.index = None
            self.metadata = []
            logger.info(f"Deleted FAISS collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error deleting FAISS collection: {e}")
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        return {
            'name': self.collection_name,
            'vectors_count': self.index.ntotal if self.index else 0,
            'status': 'active',
            'type': 'faiss'
        }
    
    def _save_index(self):
        """Save index and metadata to disk"""
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")


class VectorIndexManager:
    def __init__(self):
        self.collections: Dict[str, FAISSIndex] = {}
    
    def get_collection(self, collection_name: str) -> FAISSIndex:
        """Get or create a collection"""
        if collection_name not in self.collections:
            self.collections[collection_name] = FAISSIndex(collection_name)
        return self.collections[collection_name]
    
    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        if collection_name in self.collections:
            self.collections[collection_name].delete_collection()
            del self.collections[collection_name]
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections"""
        return [
            collection.get_collection_info()
            for collection in self.collections.values()
        ]


# Global vector index manager
vector_index_manager = VectorIndexManager()
