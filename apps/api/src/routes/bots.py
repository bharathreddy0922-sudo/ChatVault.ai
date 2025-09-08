import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..deps import get_session
from ..models import Bot, BotCreate, BotRead

router = APIRouter(prefix="/bots", tags=["bots"])


@router.post("/", response_model=BotRead)
def create_bot(bot_data: BotCreate, session: Session = Depends(get_session)):
    """Create a new bot"""
    try:
        # Generate a unique slug
        slug = f"{bot_data.name.lower().replace(' ', '-')}-{str(uuid.uuid4())[:8]}"
        
        # Check if slug already exists
        existing_bot = session.exec(select(Bot).where(Bot.slug == slug)).first()
        if existing_bot:
            # Generate a different slug
            slug = f"{bot_data.name.lower().replace(' ', '-')}-{str(uuid.uuid4())[:8]}"
        
        bot = Bot(
            name=bot_data.name,
            description=bot_data.description,
            owner=bot_data.owner,
            slug=slug
        )
        
        session.add(bot)
        session.commit()
        session.refresh(bot)
        
        return bot
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating bot: {str(e)}")


@router.get("/", response_model=List[BotRead])
def list_bots(session: Session = Depends(get_session)):
    """List all bots"""
    try:
        bots = session.exec(select(Bot).order_by(Bot.created_at.desc())).all()
        return bots
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing bots: {str(e)}")


@router.get("/{bot_id}", response_model=BotRead)
def get_bot(bot_id: int, session: Session = Depends(get_session)):
    """Get a specific bot"""
    try:
        bot = session.get(Bot, bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        return bot
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting bot: {str(e)}")


@router.get("/slug/{slug}", response_model=BotRead)
def get_bot_by_slug(slug: str, session: Session = Depends(get_session)):
    """Get a bot by its slug"""
    try:
        bot = session.exec(select(Bot).where(Bot.slug == slug)).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        return bot
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting bot: {str(e)}")


@router.delete("/{bot_id}")
def delete_bot(bot_id: int, session: Session = Depends(get_session)):
    """Delete a bot and all its associated data"""
    try:
        bot = session.get(Bot, bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Delete associated documents, chunks, chats, etc.
        from ..models import Document, Chunk, Chat, UrlSource
        
        # Delete chunks
        session.exec(select(Chunk).where(Chunk.bot_id == bot_id)).all()
        
        # Delete documents
        documents = session.exec(select(Document).where(Document.bot_id == bot_id)).all()
        for doc in documents:
            # Delete files
            import os
            if doc.path_original and os.path.exists(doc.path_original):
                os.remove(doc.path_original)
            if doc.path_parsed and os.path.exists(doc.path_parsed):
                os.remove(doc.path_parsed)
        
        # Delete URL sources
        session.exec(select(UrlSource).where(UrlSource.bot_id == bot_id)).all()
        
        # Delete chats and messages
        chats = session.exec(select(Chat).where(Chat.bot_id == bot_id)).all()
        for chat in chats:
            from ..models import Message
            session.exec(select(Message).where(Message.chat_id == chat.id)).all()
        
        # Delete the bot
        session.delete(bot)
        session.commit()
        
        return {"message": "Bot deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting bot: {str(e)}")
