import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select
from ..deps import get_session
from ..models import Document, DocumentCreate, DocumentRead, UploadResponse
from ..config import settings
from ..utils.tasks import task_manager

router = APIRouter(prefix="/bots", tags=["uploads"])


@router.post("/{bot_id}/add-docs", response_model=UploadResponse)
async def upload_documents(
    bot_id: int,
    files: List[UploadFile] = File(...),
    session: Session = Depends(get_session)
):
    """Upload documents to a bot"""
    try:
        # Check if bot exists
        from ..models import Bot
        bot = session.get(Bot, bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Validate files
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 10:  # Limit number of files
            raise HTTPException(status_code=400, detail="Too many files (max 10)")
        
        # Process each file
        task_ids = []
        for file in files:
            # Validate file type
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in settings.allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File type {file_ext} not allowed. Allowed: {settings.allowed_extensions}"
                )
            
            # Check file size
            if file.size > settings.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} too large (max {settings.max_file_size / 1024 / 1024}MB)"
                )
            
            # Sanitize filename
            safe_filename = _sanitize_filename(file.filename)
            file_path = os.path.join(settings.upload_dir, f"{bot_id}_{safe_filename}")
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Create document record
            document = Document(
                bot_id=bot_id,
                filename=safe_filename,
                filetype=file_ext,
                path_original=file_path,
                status="PENDING"
            )
            
            session.add(document)
            session.commit()
            session.refresh(document)
            
            # Start background processing
            async def process_doc():
                from ..services.parsing import DocumentParser
                from ..services.chunking import SemanticChunker
                from ..services.embed import EmbeddingService
                from ..services.index import VectorIndex
                
                try:
                    # Parse document
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
                    chunker = SemanticChunker()
                    chunks_data = chunker.chunk_text(parsed_data['text'], {
                        'document_id': document.id,
                        'page_content': parsed_data.get('page_content', [])
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
                    
                    # Update document status
                    document.status = "DONE"
                    session.commit()
                    
                    return {
                        'status': 'success',
                        'document_id': document.id,
                        'chunks_created': len(chunks),
                        'collection': collection_name
                    }
                    
                except Exception as e:
                    document.status = "ERROR"
                    session.commit()
                    raise e
            
            task_id = await task_manager.submit_task(
                "process_document",
                {"document_id": document.id, "bot_id": bot_id},
                process_doc,
                session
            )
            task_ids.append(task_id)
        
        return UploadResponse(
            task_id=",".join(task_ids),
            message=f"Uploaded {len(files)} documents. Processing started."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading documents: {str(e)}")


@router.get("/{bot_id}/documents", response_model=List[DocumentRead])
def list_documents(bot_id: int, session: Session = Depends(get_session)):
    """List all documents for a bot"""
    try:
        # Check if bot exists
        from ..models import Bot
        bot = session.get(Bot, bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        documents = session.exec(
            select(Document).where(Document.bot_id == bot_id).order_by(Document.created_at.desc())
        ).all()
        
        return documents
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@router.delete("/{bot_id}/documents/{document_id}")
def delete_document(bot_id: int, document_id: int, session: Session = Depends(get_session)):
    """Delete a document"""
    try:
        # Check if bot exists
        from ..models import Bot
        bot = session.get(Bot, bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Get document
        document = session.get(Document, document_id)
        if not document or document.bot_id != bot_id:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete associated chunks
        from ..models import Chunk
        chunks = session.exec(select(Chunk).where(Chunk.document_id == document_id)).all()
        for chunk in chunks:
            session.delete(chunk)
        
        # Delete files
        if document.path_original and os.path.exists(document.path_original):
            os.remove(document.path_original)
        if document.path_parsed and os.path.exists(document.path_parsed):
            os.remove(document.path_parsed)
        
        # Delete document
        session.delete(document)
        session.commit()
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    import uuid
    
    # Remove or replace unsafe characters
    safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Ensure unique filename
    name, ext = os.path.splitext(safe_filename)
    unique_filename = f"{name}_{str(uuid.uuid4())[:8]}{ext}"
    
    return unique_filename
