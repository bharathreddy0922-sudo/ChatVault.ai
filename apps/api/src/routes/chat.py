import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from ..deps import get_session
from ..models import Bot, Chat, Message, ChatRequest, ChatResponse
from ..services.embed import EmbeddingService
from ..services.index import VectorIndex
from ..services.rag import RAGService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/{slug}")
async def chat_with_bot(
    slug: str,
    chat_request: ChatRequest,
    request: Request,
    session: Session = Depends(get_session)
):
    """Chat with a bot using RAG"""
    try:
        # Get bot by slug
        bot = session.exec(select(Bot).where(Bot.slug == slug)).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Get or create chat
        chat_id = chat_request.chat_id
        if not chat_id:
            chat = Chat(bot_id=bot.id)
            session.add(chat)
            session.commit()
            session.refresh(chat)
            chat_id = chat.id
        else:
            chat = session.get(Chat, chat_id)
            if not chat or chat.bot_id != bot.id:
                raise HTTPException(status_code=404, detail="Chat not found")
        
        # Save user message
        user_message = Message(
            chat_id=chat_id,
            role="user",
            content=chat_request.message
        )
        session.add(user_message)
        session.commit()
        
        # Get chat history
        chat_history = session.exec(
            select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
        ).all()
        
        # Convert to format expected by RAG service
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in chat_history[:-1]  # Exclude the current user message
        ]
        
        # Retrieve relevant chunks
        embedder = EmbeddingService()
        vector_index = VectorIndex()
        
        # Embed the query
        query_embedding = embedder.embed_text(chat_request.message)
        
        # Search for relevant chunks
        collection_name = f"bot_{bot.id}"
        retrieved_chunks = vector_index.search(
            collection_name, 
            query_embedding, 
            top_k=8
        )
        
        if not retrieved_chunks:
            # No relevant chunks found
            response_text = "I cannot find information about this in the provided documents."
            sources = []
        else:
            # Generate response using RAG
            rag_service = RAGService()
            
            # Create a generator for streaming
            def generate_response():
                response_text = ""
                for chunk in rag_service.generate_response(
                    chat_request.message, retrieved_chunks, history
                ):
                    response_text += chunk
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Extract citations
                citations = rag_service.extract_citations(response_text, retrieved_chunks)
                sources = rag_service.format_sources(citations)
                
                # Send final data with sources
                yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"
            
            return StreamingResponse(
                generate_response(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        
        # For non-streaming fallback
        response_text = "I cannot find information about this in the provided documents."
        sources = []
        
        # Save assistant message
        assistant_message = Message(
            chat_id=chat_id,
            role="assistant",
            content=response_text,
            sources=sources
        )
        session.add(assistant_message)
        session.commit()
        
        return ChatResponse(
            message=response_text,
            sources=sources,
            chat_id=chat_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")


@router.get("/{slug}/history")
def get_chat_history(slug: str, chat_id: int, session: Session = Depends(get_session)):
    """Get chat history"""
    try:
        # Get bot by slug
        bot = session.exec(select(Bot).where(Bot.slug == slug)).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Get chat
        chat = session.get(Chat, chat_id)
        if not chat or chat.bot_id != bot.id:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        # Get messages
        messages = session.exec(
            select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
        ).all()
        
        return messages
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat history: {str(e)}")


@router.get("/{slug}/chats")
def list_chats(slug: str, session: Session = Depends(get_session)):
    """List all chats for a bot"""
    try:
        # Get bot by slug
        bot = session.exec(select(Bot).where(Bot.slug == slug)).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Get chats
        chats = session.exec(
            select(Chat).where(Chat.bot_id == bot.id).order_by(Chat.created_at.desc())
        ).all()
        
        return chats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing chats: {str(e)}")


@router.delete("/{slug}/chats/{chat_id}")
def delete_chat(slug: str, chat_id: int, session: Session = Depends(get_session)):
    """Delete a chat"""
    try:
        # Get bot by slug
        bot = session.exec(select(Bot).where(Bot.slug == slug)).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Get chat
        chat = session.get(Chat, chat_id)
        if not chat or chat.bot_id != bot.id:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        # Delete messages
        messages = session.exec(select(Message).where(Message.chat_id == chat_id)).all()
        for message in messages:
            session.delete(message)
        
        # Delete chat
        session.delete(chat)
        session.commit()
        
        return {"message": "Chat deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting chat: {str(e)}")
