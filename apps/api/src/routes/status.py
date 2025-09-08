from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..deps import get_session
from ..models import Bot, Document, UrlSource, StatusResponse
from ..utils.tasks import task_manager

router = APIRouter(prefix="/bots", tags=["status"])


@router.get("/{bot_id}/status", response_model=StatusResponse)
def get_bot_status(bot_id: int, session: Session = Depends(get_session)):
    """Get the status of all documents and URLs for a bot"""
    try:
        # Check if bot exists
        bot = session.get(Bot, bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Get documents
        documents = session.exec(
            select(Document).where(Document.bot_id == bot_id)
        ).all()
        
        # Get URL sources
        url_sources = session.exec(
            select(UrlSource).where(UrlSource.bot_id == bot_id)
        ).all()
        
        # Calculate overall status
        total_items = len(documents) + len(url_sources)
        if total_items == 0:
            return StatusResponse(
                status="NO_CONTENT",
                progress=100,
                message="No documents or URLs added yet"
            )
        
        completed_items = 0
        error_items = 0
        pending_items = 0
        
        for doc in documents:
            if doc.status == "DONE":
                completed_items += 1
            elif doc.status == "ERROR":
                error_items += 1
            else:
                pending_items += 1
        
        for url in url_sources:
            if url.status == "DONE":
                completed_items += 1
            elif url.status == "ERROR":
                error_items += 1
            else:
                pending_items += 1
        
        progress = (completed_items / total_items) * 100 if total_items > 0 else 0
        
        if error_items > 0:
            status = "ERROR"
            message = f"{error_items} items failed, {completed_items} completed"
        elif pending_items > 0:
            status = "PROCESSING"
            message = f"{pending_items} items processing, {completed_items} completed"
        else:
            status = "DONE"
            message = f"All {completed_items} items completed"
        
        return StatusResponse(
            status=status,
            progress=progress,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting bot status: {str(e)}")


@router.get("/task/{task_id}", response_model=StatusResponse)
def get_task_status_endpoint(task_id: str, session: Session = Depends(get_session)):
    """Get the status of a specific task"""
    try:
        status_data = task_manager.get_task_status(task_id, session)
        if not status_data:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return StatusResponse(
            status=status_data['status'],
            progress=100 if status_data['status'] == 'COMPLETED' else 0,
            message=status_data.get('error', 'Task completed successfully')
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting task status: {str(e)}")


@router.get("/{bot_id}/documents/status")
def get_documents_status(bot_id: int, session: Session = Depends(get_session)):
    """Get detailed status of all documents for a bot"""
    try:
        # Check if bot exists
        bot = session.get(Bot, bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Get documents with status
        documents = session.exec(
            select(Document).where(Document.bot_id == bot_id).order_by(Document.created_at.desc())
        ).all()
        
        return [
            {
                "id": doc.id,
                "filename": doc.filename,
                "status": doc.status,
                "created_at": doc.created_at,
                "pages": doc.pages
            }
            for doc in documents
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting documents status: {str(e)}")


@router.get("/{bot_id}/urls/status")
def get_urls_status(bot_id: int, session: Session = Depends(get_session)):
    """Get detailed status of all URL sources for a bot"""
    try:
        # Check if bot exists
        bot = session.get(Bot, bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Get URL sources with status
        url_sources = session.exec(
            select(UrlSource).where(UrlSource.bot_id == bot_id).order_by(UrlSource.created_at.desc())
        ).all()
        
        return [
            {
                "id": url.id,
                "root_url": url.root_url,
                "status": url.status,
                "created_at": url.created_at,
                "fetched_urls_count": len(url.fetched_urls) if url.fetched_urls else 0
            }
            for url in url_sources
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting URLs status: {str(e)}")
