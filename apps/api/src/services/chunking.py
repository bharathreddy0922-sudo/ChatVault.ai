import re
import tiktoken
from typing import List, Dict, Any, Optional
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class SemanticChunker:
    def __init__(self):
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk text semantically with overlap and heading detection"""
        try:
            # Extract page content if available
            page_content = metadata.get('page_content', [])
            
            if page_content:
                return self._chunk_by_pages(page_content, metadata)
            else:
                return self._chunk_by_semantic_boundaries(text, metadata)
                
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            # Fallback to simple chunking
            return self._simple_chunk(text, metadata)
    
    def _chunk_by_pages(self, page_content: List[Dict[str, Any]], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk by pages with semantic boundaries within each page"""
        chunks = []
        
        for page_data in page_content:
            page_num = page_data.get('page', 1)
            page_text = page_data.get('text', '')
            page_type = page_data.get('type', 'text')
            
            if not page_text.strip():
                continue
            
            # Chunk the page text
            page_chunks = self._chunk_by_semantic_boundaries(
                page_text, 
                metadata, 
                page_num=page_num,
                page_type=page_type
            )
            
            chunks.extend(page_chunks)
        
        return chunks
    
    def _chunk_by_semantic_boundaries(self, text: str, metadata: Dict[str, Any], 
                                    page_num: Optional[int] = None, 
                                    page_type: str = 'text') -> List[Dict[str, Any]]:
        """Chunk text by semantic boundaries (headings, paragraphs, etc.)"""
        chunks = []
        
        # Split by headings and major sections
        sections = self._split_by_headings(text)
        
        for i, section in enumerate(sections):
            if not section['text'].strip():
                continue
            
            # Further split large sections
            if len(self.tokenizer.encode(section['text'])) > self.chunk_size:
                sub_chunks = self._split_large_section(section['text'], section['headings'])
                for j, sub_chunk in enumerate(sub_chunks):
                    chunk_data = self._create_chunk_data(
                        sub_chunk, metadata, page_num, page_type,
                        section['headings'], f"{i}_{j}"
                    )
                    chunks.append(chunk_data)
            else:
                chunk_data = self._create_chunk_data(
                    section['text'], metadata, page_num, page_type,
                    section['headings'], str(i)
                )
                chunks.append(chunk_data)
        
        # Apply overlap between chunks
        return self._apply_overlap(chunks)
    
    def _split_by_headings(self, text: str) -> List[Dict[str, Any]]:
        """Split text by headings and major sections"""
        sections = []
        
        # Common heading patterns
        heading_patterns = [
            r'^#{1,6}\s+(.+)$',  # Markdown headings
            r'^[A-Z][A-Z\s]{2,}$',  # ALL CAPS headings
            r'^\d+\.\s+[A-Z][^.]*$',  # Numbered headings
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*$',  # Title Case headings
        ]
        
        lines = text.split('\n')
        current_section = {'text': '', 'headings': []}
        
        for line in lines:
            is_heading = False
            
            for pattern in heading_patterns:
                if re.match(pattern, line.strip()):
                    # Save current section if it has content
                    if current_section['text'].strip():
                        sections.append(current_section)
                    
                    # Start new section
                    current_section = {
                        'text': line + '\n',
                        'headings': [line.strip()]
                    }
                    is_heading = True
                    break
            
            if not is_heading:
                current_section['text'] += line + '\n'
        
        # Add the last section
        if current_section['text'].strip():
            sections.append(current_section)
        
        return sections
    
    def _split_large_section(self, text: str, headings: List[str]) -> List[str]:
        """Split large sections into smaller chunks"""
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        current_chunk = ''
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
            
            # Check if adding this paragraph would exceed chunk size
            test_chunk = current_chunk + '\n\n' + paragraph if current_chunk else paragraph
            token_count = len(self.tokenizer.encode(test_chunk))
            
            if token_count > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk = test_chunk
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _create_chunk_data(self, text: str, metadata: Dict[str, Any], 
                          page_num: Optional[int], page_type: str,
                          headings: List[str], section_id: str) -> Dict[str, Any]:
        """Create chunk data with metadata"""
        chunk_id = f"chunk_{metadata.get('document_id', 'unknown')}_{page_num or 1}_{section_id}"
        
        location = {
            'page': page_num,
            'type': page_type,
            'section': section_id
        }
        
        return {
            'chunk_id': chunk_id,
            'text': text,
            'location': location,
            'headings': headings,
            'token_count': len(self.tokenizer.encode(text))
        }
    
    def _apply_overlap(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply overlap between chunks"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i > 0:
                # Add overlap from previous chunk
                prev_chunk = chunks[i-1]
                overlap_text = self._get_overlap_text(prev_chunk['text'], self.chunk_overlap)
                
                if overlap_text:
                    chunk['text'] = overlap_text + '\n\n' + chunk['text']
                    chunk['token_count'] = len(self.tokenizer.encode(chunk['text']))
            
            overlapped_chunks.append(chunk)
        
        return overlapped_chunks
    
    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """Get the last N tokens as overlap text"""
        tokens = self.tokenizer.encode(text)
        
        if len(tokens) <= overlap_tokens:
            return text
        
        # Get the last N tokens
        overlap_tokens_list = tokens[-overlap_tokens:]
        overlap_text = self.tokenizer.decode(overlap_tokens_list)
        
        # Try to break at a sentence boundary
        sentences = re.split(r'[.!?]+', overlap_text)
        if len(sentences) > 1:
            # Return everything except the last incomplete sentence
            return '. '.join(sentences[:-1]) + '.'
        
        return overlap_text
    
    def _simple_chunk(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simple chunking fallback"""
        chunks = []
        tokens = self.tokenizer.encode(text)
        
        for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
            chunk_tokens = tokens[i:i + self.chunk_size]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            chunk_data = {
                'chunk_id': f"simple_chunk_{metadata.get('document_id', 'unknown')}_{i//self.chunk_size}",
                'text': chunk_text,
                'location': {'page': 1, 'type': 'text', 'section': str(i//self.chunk_size)},
                'headings': [],
                'token_count': len(chunk_tokens)
            }
            
            chunks.append(chunk_data)
        
        return chunks
