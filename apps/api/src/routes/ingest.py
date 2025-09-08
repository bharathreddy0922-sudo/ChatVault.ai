from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..deps import get_session
from ..models import Bot, UrlSource, UrlSourceCreate, UrlSourceRead, UploadResponse
from ..utils.tasks import task_manager

router = APIRouter(prefix="/bots", tags=["ingest"])


@router.post("/{bot_id}/add-urls", response_model=UploadResponse)
async def add_urls(
    bot_id: int,
    url_data: UrlSourceCreate,
    session: Session = Depends(get_session)
):
    """Add URLs for crawling"""
    try:
        # Check if bot exists
        bot = session.get(Bot, bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Create URL source
        url_source = UrlSource(
            bot_id=bot_id,
            root_url=url_data.root_url,
            depth=url_data.depth
        )
        
        session.add(url_source)
        session.commit()
        session.refresh(url_source)
        
        # Start background processing
        async def process_url_task():
            from ..services.crawl import WebCrawler
            from ..services.chunking import SemanticChunker
            from ..services.embed import EmbeddingService
            from ..services.index import VectorIndex
            from ..models import Document, Chunk
            
            try:
                # Crawl URL
                crawler = WebCrawler()
                crawled_data = await crawler.crawl_url(url_source.root_url, url_source.depth)
                
                # Process crawled content
                content_text = crawler.process_crawled_content(crawled_data)
                
                # Create a virtual document for the crawled content
                document = Document(
                    bot_id=bot_id,
                    filename=f"crawled_{url_source.id}.txt",
                    filetype=".txt",
                    path_original=f"crawled_{url_source.id}.txt",
                    path_parsed=f"crawled_{url_source.id}.txt",
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
                embedder = EmbeddingService()
                embedded_chunks = embedder.embed_chunks(chunks_data)
                
                # Index chunks
                vector_index = VectorIndex()
                collection_name = f"bot_{bot_id}"
                embedding_dim = embedder.get_embedding_dimension()
                vector_index.create_collection(collection_name, embedding_dim)
                vector_index.add_chunks(collection_name, embedded_chunks)
                
                # Update statuses
                document.status = "DONE"
                url_source.status = "DONE"
                url_source.fetched_urls = [url['url'] for url in crawled_data['crawled_urls']]
                session.commit()
                
                return {
                    'status': 'success',
                    'url_source_id': url_source.id,
                    'document_id': document.id,
                    'chunks_created': len(chunks),
                    'urls_crawled': len(crawled_data['crawled_urls'])
                }
                
            except Exception as e:
                url_source.status = "ERROR"
                session.commit()
                raise e
        
        task_id = await task_manager.submit_task(
            "process_url",
            {"url_source_id": url_source.id, "bot_id": bot_id},
            process_url_task,
            session
        )
        
        return UploadResponse(
            task_id=task_id,
            message=f"URL {url_data.root_url} added for crawling. Processing started."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding URL: {str(e)}")


@router.get("/{bot_id}/urls", response_model=List[UrlSourceRead])
def list_urls(bot_id: int, session: Session = Depends(get_session)):
    """List all URL sources for a bot"""
    try:
        # Check if bot exists
        bot = session.get(Bot, bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        url_sources = session.exec(
            select(UrlSource).where(UrlSource.bot_id == bot_id).order_by(UrlSource.created_at.desc())
        ).all()
        
        return url_sources
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing URLs: {str(e)}")


@router.delete("/{bot_id}/urls/{url_id}")
def delete_url(bot_id: int, url_id: int, session: Session = Depends(get_session)):
    """Delete a URL source"""
    try:
        # Check if bot exists
        bot = session.get(Bot, bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Get URL source
        url_source = session.get(UrlSource, url_id)
        if not url_source or url_source.bot_id != bot_id:
            raise HTTPException(status_code=404, detail="URL source not found")
        
        # Delete URL source
        session.delete(url_source)
        session.commit()
        
        return {"message": "URL source deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting URL source: {str(e)}")
