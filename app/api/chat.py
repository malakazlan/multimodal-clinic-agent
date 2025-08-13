"""
Chat API routes for the Healthcare Voice AI Assistant.
Handles RAG-based conversations with healthcare safety features.
"""

import time
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from rag.rag_pipeline import RAGPipeline
from llm.openai_client import OpenAILLMClient
from safety.healthcare_filter import HealthcareSafetyFilter
from memory.conversation_memory import ConversationMemory
from utils.logger import logger, log_rag_query, log_user_interaction
from config.settings import get_settings

router = APIRouter()

# Initialize components
rag_pipeline = RAGPipeline()
llm_client = OpenAILLMClient()
safety_filter = HealthcareSafetyFilter()
memory = ConversationMemory()


class ChatMessage(BaseModel):
    """Individual chat message."""
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[float] = Field(default=None, description="Timestamp of the message")


class ChatRequest(BaseModel):
    """Request model for chat conversation."""
    message: str = Field(..., description="User's message", min_length=1, max_length=1000)
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for continuity")
    user_id: Optional[str] = Field(default="anonymous", description="User identifier")
    include_context: bool = Field(default=True, description="Whether to include RAG context")
    stream: bool = Field(default=False, description="Whether to stream the response")


class ChatResponse(BaseModel):
    """Response model for chat conversation."""
    response: str = Field(..., description="AI assistant's response")
    conversation_id: str = Field(..., description="Conversation ID for continuity")
    context_sources: List[dict] = Field(default=[], description="Sources used for RAG context")
    safety_checks: dict = Field(..., description="Safety check results")
    processing_time: float = Field(..., description="Total processing time in seconds")
    disclaimer: Optional[str] = Field(default=None, description="Healthcare disclaimer if applicable")


class ConversationHistory(BaseModel):
    """Model for conversation history."""
    conversation_id: str
    messages: List[ChatMessage]
    created_at: float
    updated_at: float
    user_id: str


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message and get AI response with RAG context.
    
    Args:
        request: ChatRequest with user message and parameters
        
    Returns:
        ChatResponse with AI response and metadata
    """
    start_time = time.time()
    settings = get_settings()
    
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid4())
        
        # Log user interaction
        log_user_interaction(
            user_id=request.user_id,
            action="send_message",
            details={
                "conversation_id": conversation_id,
                "message_length": len(request.message),
                "include_context": request.include_context
            }
        )
        
        # Safety check on user input
        safety_result = await safety_filter.check_content(
            content=request.message,
            content_type="user_input"
        )
        
        if not safety_result.is_safe:
            logger.warning(f"Unsafe user input detected: {safety_result.risk_level}")
            raise HTTPException(
                status_code=400,
                detail=f"Message contains inappropriate content: {safety_result.reason}"
            )
        
        # Get conversation history
        conversation_history = await memory.get_conversation(conversation_id)
        
        # Prepare context from RAG if requested
        context_sources = []
        if request.include_context:
            rag_start = time.time()
            
            # Perform RAG query
            rag_results = await rag_pipeline.query(
                query=request.message,
                top_k=settings.top_k_results,
                similarity_threshold=settings.similarity_threshold
            )
            
            rag_time = time.time() - rag_start
            
            # Log RAG query
            log_rag_query(
                query=request.message,
                results_count=len(rag_results.documents),
                response_time_ms=rag_time * 1000,
                top_results=[doc.metadata for doc in rag_results.documents[:3]]
            )
            
            context_sources = [
                {
                    "title": doc.metadata.get("title", "Unknown"),
                    "source": doc.metadata.get("source", "Unknown"),
                    "relevance_score": doc.relevance_score,
                    "snippet": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
                }
                for doc in rag_results.documents
            ]
        
        # Prepare conversation context for LLM
        messages = []
        
        # Add system message with healthcare context
        system_message = create_system_message(context_sources)
        messages.append({"role": "system", "content": system_message})
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history.messages[-settings.max_conversation_history:]:
                messages.append({"role": msg.role, "content": msg.content})
        
        # Add current user message
        messages.append({"role": "user", "content": request.message})
        
        # Generate LLM response
        llm_start = time.time()
        llm_response = await llm_client.generate_response(
            messages=messages,
            max_tokens=settings.openai_max_tokens,
            temperature=settings.openai_temperature
        )
        llm_time = time.time() - llm_start
        
        # Safety check on AI response
        response_safety = await safety_filter.check_content(
            content=llm_response,
            content_type="ai_response"
        )
        
        if not response_safety.is_safe:
            logger.warning(f"Unsafe AI response detected: {response_safety.risk_level}")
            # Generate safe fallback response
            llm_response = await safety_filter.generate_safe_response(request.message)
        
        # Add healthcare disclaimer if required
        disclaimer = None
        if settings.require_disclaimer and settings.healthcare_disclaimer:
            disclaimer = get_healthcare_disclaimer()
            llm_response += f"\n\n{disclaimer}"
        
        # Store conversation in memory
        user_message = ChatMessage(
            role="user",
            content=request.message,
            timestamp=time.time()
        )
        
        assistant_message = ChatMessage(
            role="assistant",
            content=llm_response,
            timestamp=time.time()
        )
        
        await memory.add_message(conversation_id, user_message)
        await memory.add_message(conversation_id, assistant_message)
        
        total_time = time.time() - start_time
        
        # Log performance metrics
        logger.info(f"Chat processing completed in {total_time:.3f}s", extra={
            "rag_time": rag_time if request.include_context else 0,
            "llm_time": llm_time,
            "total_time": total_time,
            "conversation_id": conversation_id
        })
        
        return ChatResponse(
            response=llm_response,
            conversation_id=conversation_id,
            context_sources=context_sources,
            safety_checks={
                "user_input_safe": safety_result.is_safe,
                "ai_response_safe": response_safety.is_safe,
                "risk_level": max(safety_result.risk_level, response_safety.risk_level)
            },
            processing_time=total_time,
            disclaimer=disclaimer
        )
        
    except HTTPException:
        raise
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Chat processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.get("/history/{conversation_id}", response_model=ConversationHistory)
async def get_conversation_history(conversation_id: str):
    """
    Get conversation history for a specific conversation.
    
    Args:
        conversation_id: ID of the conversation to retrieve
        
    Returns:
        ConversationHistory with all messages
    """
    try:
        conversation = await memory.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation history")


@router.delete("/history/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation and its history.
    
    Args:
        conversation_id: ID of the conversation to delete
    """
    try:
        await memory.delete_conversation(conversation_id)
        return {"message": "Conversation deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete conversation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete conversation")


@router.get("/conversations")
async def list_conversations(user_id: str = "anonymous", limit: int = 10):
    """
    List recent conversations for a user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of conversations to return
        
    Returns:
        List of conversation summaries
    """
    try:
        conversations = await memory.list_conversations(user_id, limit)
        return {"conversations": conversations}
    except Exception as e:
        logger.error(f"Failed to list conversations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list conversations")


def create_system_message(context_sources: List[dict]) -> str:
    """Create system message with healthcare context and RAG information."""
    base_message = """You are a healthcare information assistant. Your role is to provide accurate, helpful information based on the provided context. 

IMPORTANT SAFETY RULES:
1. Never provide medical advice, diagnosis, or treatment recommendations
2. Always encourage users to consult healthcare professionals for medical concerns
3. Focus on providing educational information and general guidance
4. If asked about symptoms, treatments, or medical procedures, refer to healthcare providers
5. Be clear about the limitations of your knowledge and the importance of professional medical consultation

You have access to the following healthcare information sources:"""

    if context_sources:
        context_text = "\n\n".join([
            f"- {source['title']} (Source: {source['source']}, Relevance: {source['relevance_score']:.2f})"
            for source in context_sources
        ])
        base_message += f"\n\n{context_text}\n\nUse this information to provide helpful, accurate responses while following all safety guidelines."
    else:
        base_message += "\n\nNo specific context available. Provide general healthcare information while following all safety guidelines."
    
    return base_message


def get_healthcare_disclaimer() -> str:
    """Get standard healthcare disclaimer."""
    return """⚠️ DISCLAIMER: This information is for educational purposes only and should not be considered medical advice. Always consult with qualified healthcare professionals for medical concerns, diagnosis, and treatment. The information provided does not replace professional medical consultation."""
