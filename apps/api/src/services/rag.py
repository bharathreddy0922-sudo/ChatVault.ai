import json
import logging
from typing import List, Dict, Any, Optional, Generator
import httpx
from ..config import settings

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.ollama_url = settings.ollama_url
        self.model = settings.ollama_model
    
    def generate_response(self, query: str, retrieved_chunks: List[Dict[str, Any]], 
                         chat_history: List[Dict[str, Any]] = None) -> Generator[str, None, None]:
        """Generate RAG response with streaming"""
        try:
            # Build the prompt
            prompt = self._build_prompt(query, retrieved_chunks, chat_history)
            
            # Call Ollama with streaming
            for chunk in self._call_ollama_stream(prompt):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            yield f"Error: {str(e)}"
    
    def _build_prompt(self, query: str, retrieved_chunks: List[Dict[str, Any]], 
                     chat_history: List[Dict[str, Any]] = None) -> str:
        """Build the RAG prompt"""
        
        # System message
        system_prompt = """You are a source-grounded research assistant. Your responses must be based ONLY on the provided context. 

IMPORTANT RULES:
1. Only answer using information from the provided CONTEXT
2. If the answer is not found in the context, say "I cannot find information about this in the provided documents."
3. Always include inline citations like [1], [2], [3] that reference the source chunks
4. Be concise but thorough
5. If comparing multiple documents, create a clear comparison with citations
6. Do not make up or infer information not present in the context"""

        # Build context from retrieved chunks
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            source_info = f"[{i}] Source: "
            if chunk.get('location', {}).get('page'):
                source_info += f"Page {chunk['location']['page']}"
            if chunk.get('headings'):
                source_info += f" - {' > '.join(chunk['headings'])}"
            
            context_parts.append(f"{source_info}\n{chunk['text']}\n")
        
        context = "\n".join(context_parts)
        
        # Build conversation history
        conversation = ""
        if chat_history:
            for msg in chat_history[-4:]:  # Last 4 messages
                role = "User" if msg['role'] == 'user' else "Assistant"
                conversation += f"{role}: {msg['content']}\n"
        
        # Final prompt
        prompt = f"""{system_prompt}

CONTEXT:
{context}

{conversation}User: {query}

Assistant: Based on the provided context, """
        
        return prompt
    
    def _call_ollama_stream(self, prompt: str) -> Generator[str, None, None]:
        """Call Ollama with streaming"""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": True,
                        "options": {
                            "temperature": 0.1,
                            "top_p": 0.9,
                            "max_tokens": 2000
                        }
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if 'response' in data:
                                yield data['response']
                            if data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            yield f"Error calling language model: {str(e)}"
    
    def _call_ollama_sync(self, prompt: str) -> str:
        """Call Ollama synchronously (non-streaming)"""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "top_p": 0.9,
                            "max_tokens": 2000
                        }
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
                data = response.json()
                return data.get('response', '')
                
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return f"Error calling language model: {str(e)}"
    
    def extract_citations(self, response: str, retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract citations from the response"""
        citations = []
        
        # Find citation patterns like [1], [2], etc.
        import re
        citation_pattern = r'\[(\d+)\]'
        matches = re.findall(citation_pattern, response)
        
        for match in matches:
            try:
                chunk_index = int(match) - 1  # Convert to 0-based index
                if 0 <= chunk_index < len(retrieved_chunks):
                    chunk = retrieved_chunks[chunk_index]
                    citation = {
                        'chunk_id': chunk['chunk_id'],
                        'document_id': chunk.get('document_id'),
                        'location': chunk['location'],
                        'headings': chunk.get('headings', []),
                        'text': chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text']
                    }
                    citations.append(citation)
            except (ValueError, IndexError):
                continue
        
        return citations
    
    def format_sources(self, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format citations for API response"""
        sources = []
        
        for citation in citations:
            source = {
                'document_id': citation['document_id'],
                'location': citation['location'],
                'headings': citation['headings'],
                'snippet': citation['text']
            }
            sources.append(source)
        
        return sources
