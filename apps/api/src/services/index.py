import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from ..config import settings
from .index_faiss import vector_index_manager

logger = logging.getLogger(__name__)

# Try to import Qdrant (optional)
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.info("Qdrant not available, using FAISS only")


class VectorIndex:
    def __init__(self):
        self.qdrant_client = None
        self.use_qdrant = False
        self.embedding_dim = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the vector database (FAISS-first, Qdrant optional)"""
        # Always use FAISS as primary
        logger.info("Using FAISS as primary vector database")
        
        # Try to initialize Qdrant as optional secondary
        if QDRANT_AVAILABLE and settings.qdrant_url:
            try:
                self.qdrant_client = QdrantClient(
                    url=settings.qdrant_url,
                    api_key=settings.qdrant_api_key
                )
                # Test connection
                self.qdrant_client.get_collections()
                self.use_qdrant = True
                logger.info("Qdrant connected successfully (optional)")
            except Exception as e:
                logger.warning(f"Qdrant not available: {e}. Using FAISS only.")
                self.use_qdrant = False
        else:
            logger.info("Qdrant not configured, using FAISS only")
    
    def create_collection(self, collection_name: str, embedding_dim: int):
        """Create a collection (FAISS always, Qdrant optional)"""
        self.embedding_dim = embedding_dim
        
        # Always create FAISS collection
        vector_index_manager.get_collection(collection_name)
        
        # Optionally create Qdrant collection
        if self.use_qdrant:
            try:
                self.qdrant_client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {collection_name}")
            except Exception as e:
                logger.warning(f"Failed to create Qdrant collection: {e}")
    
    def add_chunks(self, collection_name: str, chunks: List[Dict[str, Any]]):
        """Add chunks to the vector database"""
        # Always add to FAISS
        faiss_collection = vector_index_manager.get_collection(collection_name)
        faiss_collection.add_chunks(chunks)
        
        # Optionally add to Qdrant
        if self.use_qdrant:
            try:
                points = []
                for chunk in chunks:
                    point = PointStruct(
                        id=chunk['chunk_id'],
                        vector=chunk['embedding'],
                        payload={
                            'text': chunk['text'],
                            'document_id': chunk.get('document_id'),
                            'location': chunk['location'],
                            'headings': chunk['headings']
                        }
                    )
                    points.append(point)
                
                self.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                logger.info(f"Added {len(chunks)} chunks to Qdrant collection: {collection_name}")
            except Exception as e:
                logger.warning(f"Failed to add chunks to Qdrant: {e}")
    
    def search(self, collection_name: str, query_embedding: List[float], 
               top_k: int = 8, filter_document_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Search for similar chunks (FAISS primary, Qdrant fallback)"""
        # Always search FAISS first
        faiss_collection = vector_index_manager.get_collection(collection_name)
        faiss_results = faiss_collection.search(query_embedding, top_k, filter_document_ids)
        
        # If we have enough results from FAISS, return them
        if len(faiss_results) >= top_k:
            return faiss_results
        
        # If Qdrant is available and we need more results, try Qdrant
        if self.use_qdrant and len(faiss_results) < top_k:
            try:
                # Create filter if document IDs are specified
                search_filter = None
                if filter_document_ids:
                    search_filter = Filter(
                        must=[
                            FieldCondition(
                                key="document_id",
                                match=MatchValue(value=doc_id)
                            ) for doc_id in filter_document_ids
                        ]
                    )
                
                qdrant_results = self.qdrant_client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    limit=top_k - len(faiss_results),
                    query_filter=search_filter,
                    with_payload=True
                )
                
                # Convert Qdrant results to same format
                for result in qdrant_results:
                    qdrant_result = {
                        'chunk_id': result.id,
                        'score': result.score,
                        'text': result.payload['text'],
                        'document_id': result.payload['document_id'],
                        'location': result.payload['location'],
                        'headings': result.payload['headings']
                    }
                    
                    # Avoid duplicates
                    if not any(r['chunk_id'] == qdrant_result['chunk_id'] for r in faiss_results):
                        faiss_results.append(qdrant_result)
                
            except Exception as e:
                logger.warning(f"Qdrant search failed: {e}")
        
        return faiss_results[:top_k]
    
    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        # Delete from FAISS
        vector_index_manager.delete_collection(collection_name)
        
        # Optionally delete from Qdrant
        if self.use_qdrant:
            try:
                self.qdrant_client.delete_collection(collection_name)
                logger.info(f"Deleted Qdrant collection: {collection_name}")
            except Exception as e:
                logger.warning(f"Failed to delete Qdrant collection: {e}")
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information"""
        # Get FAISS info
        faiss_info = vector_index_manager.get_collection(collection_name).get_collection_info()
        
        # Optionally get Qdrant info
        if self.use_qdrant:
            try:
                qdrant_info = self.qdrant_client.get_collection(collection_name)
                faiss_info['qdrant_vectors'] = qdrant_info.vectors_count
            except Exception as e:
                faiss_info['qdrant_error'] = str(e)
        
        return faiss_info
