import os
import logging
from typing import Dict, Any, List
from celery import current_task
from sqlmodel import Session, select
from ..deps import engine
from ..models import Document, Chunk, Bot
from ..services.parsing import DocumentParser
from ..services.chunking import SemanticChunker
from ..services.embed import EmbeddingService
from ..services.index import VectorIndex
from ..services.crawl import WebCrawler
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def process_document(self, document_id: int, bot_id: int):
    """Process a document through the full pipeline"""
    try:
        with Session(engine) as session:
            # Get document
            document = session.get(Document, document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Update status to PARSING
            document.status = "PARSING"
            session.commit()
            
            # Parse document
            self.update_state(state='PARSING', meta={'progress': 20})
            parser = DocumentParser()
            parsed_data = parser.parse_document(document.path_original, document.filetype)
            
            # Save parsed content
            parsed_path = f"{document.path_original}.parsed.txt"
            with open(parsed_path, 'w', encoding='utf-8') as f:
                f.write(parsed_data['text'])
            
            document.path_parsed = parsed_path
            document.pages = parsed_data.get('pages', 1)
            document.metadata.update(parsed_data.get('metadata', {}))
            document.status = "CHUNKING"
            session.commit()
            
            # Chunk document
            self.update_state(state='CHUNKING', meta={'progress': 40})
            chunker = SemanticChunker()
            chunks_data = chunker.chunk_text(parsed_data['text'], {
                'document_id': document_id,
                'page_content': parsed_data.get('page_content', [])
            })
            
            # Create chunk records
            chunks = []
            for chunk_data in chunks_data:
                chunk = Chunk(
                    bot_id=bot_id,
                    document_id=document_id,
                    chunk_id=chunk_data['chunk_id'],
                    text=chunk_data['text'],
                    location=chunk_data['location'],
                    headings=chunk_data['headings']
                )
                chunks.append(chunk)
            
            session.add_all(chunks)
            document.status = "EMBEDDING"
            session.commit()
            
            # Embed chunks
            self.update_state(state='EMBEDDING', meta={'progress': 60})
            embedder = EmbeddingService()
            embedded_chunks = embedder.embed_chunks(chunks_data)
            
            # Index chunks
            self.update_state(state='INDEXING', meta={'progress': 80})
            vector_index = VectorIndex()
            
            # Create collection if it doesn't exist
            collection_name = f"bot_{bot_id}"
            embedding_dim = embedder.get_embedding_dimension()
            vector_index.create_collection(collection_name, embedding_dim)
            
            # Add chunks to vector database
            vector_index.add_chunks(collection_name, embedded_chunks)
            
            # Update document status
            document.status = "DONE"
            session.commit()
            
            self.update_state(state='DONE', meta={'progress': 100})
            
            return {
                'status': 'success',
                'document_id': document_id,
                'chunks_created': len(chunks),
                'collection': collection_name
            }
            
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        
        # Update document status to ERROR
        with Session(engine) as session:
            document = session.get(Document, document_id)
            if document:
                document.status = "ERROR"
                session.commit()
        
        self.update_state(state='ERROR', meta={'error': str(e)})
        raise


@celery_app.task(bind=True)
def process_url(self, url_source_id: int, bot_id: int):
    """Process a URL through crawling and indexing"""
    try:
        with Session(engine) as session:
            # Get URL source
            from ..models import UrlSource
            url_source = session.get(UrlSource, url_source_id)
            if not url_source:
                raise ValueError(f"URL source {url_source_id} not found")
            
            # Update status to CRAWLING
            url_source.status = "CRAWLING"
            session.commit()
            
            # Crawl URL
            self.update_state(state='CRAWLING', meta={'progress': 30})
            crawler = WebCrawler()
            
            import asyncio
            crawled_data = asyncio.run(crawler.crawl_url(url_source.root_url, url_source.depth))
            
            # Process crawled content
            content_text = crawler.process_crawled_content(crawled_data)
            
            # Create a virtual document for the crawled content
            document = Document(
                bot_id=bot_id,
                filename=f"crawled_{url_source_id}.txt",
                filetype=".txt",
                path_original=f"crawled_{url_source_id}.txt",
                path_parsed=f"crawled_{url_source_id}.txt",
                pages=1,
                status="CHUNKING",
                metadata={
                    'source_type': 'crawled',
                    'root_url': url_source.root_url,
                    'crawled_urls': len(crawled_data['crawled_urls']),
                    'depth': url_source.depth
                }
            )
            
            session.add(document)
            session.commit()
            
            # Save crawled content
            with open(document.path_parsed, 'w', encoding='utf-8') as f:
                f.write(content_text)
            
            # Chunk content
            self.update_state(state='CHUNKING', meta={'progress': 50})
            chunker = SemanticChunker()
            chunks_data = chunker.chunk_text(content_text, {
                'document_id': document.id,
                'source_type': 'crawled'
            })
            
            # Create chunk records
            chunks = []
            for chunk_data in chunks_data:
                chunk = Chunk(
                    bot_id=bot_id,
                    document_id=document.id,
                    chunk_id=chunk_data['chunk_id'],
                    text=chunk_data['text'],
                    location=chunk_data['location'],
                    headings=chunk_data['headings']
                )
                chunks.append(chunk)
            
            session.add_all(chunks)
            document.status = "EMBEDDING"
            session.commit()
            
            # Embed chunks
            self.update_state(state='EMBEDDING', meta={'progress': 70})
            embedder = EmbeddingService()
            embedded_chunks = embedder.embed_chunks(chunks_data)
            
            # Index chunks
            self.update_state(state='INDEXING', meta={'progress': 90})
            vector_index = VectorIndex()
            
            # Create collection if it doesn't exist
            collection_name = f"bot_{bot_id}"
            embedding_dim = embedder.get_embedding_dimension()
            vector_index.create_collection(collection_name, embedding_dim)
            
            # Add chunks to vector database
            vector_index.add_chunks(collection_name, embedded_chunks)
            
            # Update statuses
            document.status = "DONE"
            url_source.status = "DONE"
            url_source.fetched_urls = [url['url'] for url in crawled_data['crawled_urls']]
            session.commit()
            
            self.update_state(state='DONE', meta={'progress': 100})
            
            return {
                'status': 'success',
                'url_source_id': url_source_id,
                'document_id': document.id,
                'chunks_created': len(chunks),
                'urls_crawled': len(crawled_data['crawled_urls'])
            }
            
    except Exception as e:
        logger.error(f"Error processing URL {url_source_id}: {e}")
        
        # Update URL source status to ERROR
        with Session(engine) as session:
            url_source = session.get(UrlSource, url_source_id)
            if url_source:
                url_source.status = "ERROR"
                session.commit()
        
        self.update_state(state='ERROR', meta={'error': str(e)})
        raise


@celery_app.task
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get the status of a Celery task"""
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            return {
                'state': 'PENDING',
                'progress': 0,
                'message': 'Task is pending'
            }
        elif task_result.state == 'SUCCESS':
            return {
                'state': 'SUCCESS',
                'progress': 100,
                'result': task_result.result
            }
        elif task_result.state == 'FAILURE':
            return {
                'state': 'FAILURE',
                'progress': 0,
                'error': str(task_result.info)
            }
        else:
            # Task is running
            info = task_result.info or {}
            return {
                'state': task_result.state,
                'progress': info.get('progress', 0),
                'message': info.get('message', 'Processing...')
            }
            
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        return {
            'state': 'ERROR',
            'progress': 0,
            'error': str(e)
        }
