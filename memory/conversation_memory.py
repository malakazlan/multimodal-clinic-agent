"""
Conversation Memory for the Healthcare Voice AI Assistant.
Manages chat history and conversation context for continuity.
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import asyncio

from loguru import logger

from config.settings import get_settings


@dataclass
class ChatMessage:
    """Individual chat message with metadata."""
    role: str  # user or assistant
    content: str
    timestamp: float
    message_id: str = None
    metadata: Dict[str, Any] = None


@dataclass
class Conversation:
    """Complete conversation with metadata."""
    conversation_id: str
    user_id: str
    messages: List[ChatMessage]
    created_at: float
    updated_at: float
    metadata: Dict[str, Any] = None


class ConversationMemory:
    """Manages conversation history and context."""
    
    def __init__(self):
        self.settings = get_settings()
        self.conversations: Dict[str, Conversation] = {}
        self.message_counter = 0
        
        # Memory TTL settings
        self.memory_ttl = timedelta(hours=self.settings.memory_ttl_hours)
        self.max_history = self.settings.max_conversation_history
        
        # Cleanup task
        self.cleanup_task = None
        self._start_cleanup_task()
        
        logger.info("Conversation memory initialized")
    
    def _start_cleanup_task(self):
        """Start background task to clean up old conversations."""
        async def cleanup():
            while True:
                try:
                    await asyncio.sleep(3600)  # Run every hour
                    await self._cleanup_expired_conversations()
                except Exception as e:
                    logger.error(f"Memory cleanup failed: {str(e)}", exc_info=True)
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self.cleanup_task = asyncio.create_task(cleanup())
        except RuntimeError:
            # No event loop running, will be started later
            pass
    
    async def add_message(
        self,
        conversation_id: str,
        message: ChatMessage,
        user_id: str = "anonymous"
    ) -> bool:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: ID of the conversation
            message: ChatMessage to add
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate message ID if not provided
            if not message.message_id:
                message.message_id = f"msg_{self.message_counter}"
                self.message_counter += 1
            
            # Get or create conversation
            if conversation_id not in self.conversations:
                conversation = Conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    messages=[],
                    created_at=time.time(),
                    updated_at=time.time(),
                    metadata={}
                )
                self.conversations[conversation_id] = conversation
            else:
                conversation = self.conversations[conversation_id]
                conversation.updated_at = time.time()
            
            # Add message
            conversation.messages.append(message)
            
            # Limit message history
            if len(conversation.messages) > self.max_history:
                conversation.messages = conversation.messages[-self.max_history:]
            
            logger.debug(f"Added message to conversation {conversation_id}: {message.role}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add message: {str(e)}", exc_info=True)
            return False
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: ID of the conversation to retrieve
            
        Returns:
            Conversation object or None if not found
        """
        try:
            conversation = self.conversations.get(conversation_id)
            
            if conversation:
                # Check if conversation has expired
                if self._is_conversation_expired(conversation):
                    logger.debug(f"Conversation {conversation_id} has expired")
                    await self.delete_conversation(conversation_id)
                    return None
                
                # Update last access time
                conversation.updated_at = time.time()
                
                return conversation
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {str(e)}", exc_info=True)
            return None
    
    async def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation summary or None if not found
        """
        try:
            conversation = await self.get_conversation(conversation_id)
            
            if not conversation:
                return None
            
            # Create summary
            summary = {
                "conversation_id": conversation.conversation_id,
                "user_id": conversation.user_id,
                "message_count": len(conversation.messages),
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
                "last_message": conversation.messages[-1].content[:100] + "..." if conversation.messages else "",
                "metadata": conversation.metadata
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get conversation summary: {str(e)}", exc_info=True)
            return None
    
    async def list_conversations(
        self,
        user_id: str = "anonymous",
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List conversations for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            
        Returns:
            List of conversation summaries
        """
        try:
            user_conversations = []
            
            for conv_id, conversation in self.conversations.items():
                if conversation.user_id == user_id:
                    # Check if conversation has expired
                    if self._is_conversation_expired(conversation):
                        continue
                    
                    summary = await self.get_conversation_summary(conv_id)
                    if summary:
                        user_conversations.append(summary)
            
            # Sort by last updated time (newest first)
            user_conversations.sort(key=lambda x: x["updated_at"], reverse=True)
            
            # Apply pagination
            return user_conversations[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to list conversations: {str(e)}", exc_info=True)
            return []
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and its messages.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
                logger.info(f"Deleted conversation: {conversation_id}")
                return True
            else:
                logger.warning(f"Conversation {conversation_id} not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {str(e)}", exc_info=True)
            return False
    
    async def clear_user_conversations(self, user_id: str) -> int:
        """
        Clear all conversations for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of conversations cleared
        """
        try:
            conversations_to_delete = []
            
            for conv_id, conversation in self.conversations.items():
                if conversation.user_id == user_id:
                    conversations_to_delete.append(conv_id)
            
            # Delete conversations
            deleted_count = 0
            for conv_id in conversations_to_delete:
                if await self.delete_conversation(conv_id):
                    deleted_count += 1
            
            logger.info(f"Cleared {deleted_count} conversations for user: {user_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to clear conversations for user {user_id}: {str(e)}", exc_info=True)
            return 0
    
    async def get_conversation_context(
        self,
        conversation_id: str,
        max_messages: int = None
    ) -> List[Dict[str, str]]:
        """
        Get conversation context for LLM processing.
        
        Args:
            conversation_id: ID of the conversation
            max_messages: Maximum number of messages to include
            
        Returns:
            List of message dictionaries with role and content
        """
        try:
            conversation = await self.get_conversation(conversation_id)
            
            if not conversation:
                return []
            
            # Use settings default if not specified
            max_messages = max_messages or self.max_history
            
            # Get recent messages
            recent_messages = conversation.messages[-max_messages:]
            
            # Convert to LLM format
            context = []
            for message in recent_messages:
                context.append({
                    "role": message.role,
                    "content": message.content
                })
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get conversation context: {str(e)}", exc_info=True)
            return []
    
    async def search_conversations(
        self,
        query: str,
        user_id: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search conversations for specific content.
        
        Args:
            query: Search query
            user_id: Optional user filter
            limit: Maximum number of results
            
        Returns:
            List of matching conversation summaries
        """
        try:
            results = []
            query_lower = query.lower()
            
            for conv_id, conversation in self.conversations.items():
                # Apply user filter if specified
                if user_id and conversation.user_id != user_id:
                    continue
                
                # Check if conversation has expired
                if self._is_conversation_expired(conversation):
                    continue
                
                # Search in messages
                for message in conversation.messages:
                    if query_lower in message.content.lower():
                        summary = await self.get_conversation_summary(conv_id)
                        if summary:
                            # Add relevance score and matching message
                            summary["relevance_score"] = 0.8  # Simple scoring
                            summary["matching_message"] = message.content[:200] + "..."
                            results.append(summary)
                            break
                
                # Limit results
                if len(results) >= limit:
                    break
            
            # Sort by relevance (simple implementation)
            results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to search conversations: {str(e)}", exc_info=True)
            return []
    
    def _is_conversation_expired(self, conversation: Conversation) -> bool:
        """Check if a conversation has expired based on TTL."""
        if not self.memory_ttl:
            return False
        
        expiration_time = conversation.updated_at + self.memory_ttl.total_seconds()
        return time.time() > expiration_time
    
    async def _cleanup_expired_conversations(self):
        """Remove expired conversations from memory."""
        try:
            expired_conversations = []
            
            for conv_id, conversation in self.conversations.items():
                if self._is_conversation_expired(conversation):
                    expired_conversations.append(conv_id)
            
            # Delete expired conversations
            deleted_count = 0
            for conv_id in expired_conversations:
                if await self.delete_conversation(conv_id):
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired conversations")
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired conversations: {str(e)}", exc_info=True)
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about conversation memory.
        
        Returns:
            Dictionary with memory statistics
        """
        try:
            total_conversations = len(self.conversations)
            total_messages = sum(len(conv.messages) for conv in self.conversations.values())
            
            # Count by user
            user_counts = {}
            for conversation in self.conversations.values():
                user_id = conversation.user_id
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
            
            # Count expired conversations
            expired_count = sum(
                1 for conv in self.conversations.values()
                if self._is_conversation_expired(conv)
            )
            
            stats = {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "active_conversations": total_conversations - expired_count,
                "expired_conversations": expired_count,
                "users_count": len(user_counts),
                "memory_ttl_hours": self.settings.memory_ttl_hours,
                "max_history": self.max_history,
                "user_distribution": user_counts
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {str(e)}", exc_info=True)
            return {}
    
    async def health_check(self) -> bool:
        """
        Perform health check on conversation memory.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Test basic operations
            test_conv_id = "health_check_test"
            test_message = ChatMessage(
                role="user",
                content="Health check message",
                timestamp=time.time()
            )
            
            # Test add message
            success = await self.add_message(test_conv_id, test_message, "test_user")
            if not success:
                return False
            
            # Test get conversation
            conversation = await self.get_conversation(test_conv_id)
            if not conversation:
                return False
            
            # Test delete conversation
            success = await self.delete_conversation(test_conv_id)
            if not success:
                return False
            
            logger.debug("Conversation memory health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Conversation memory health check failed: {str(e)}", exc_info=True)
            return False
    
    async def export_conversation(
        self,
        conversation_id: str,
        format: str = "json"
    ) -> Optional[str]:
        """
        Export a conversation to a specific format.
        
        Args:
            conversation_id: ID of the conversation to export
            format: Export format (json, txt)
            
        Returns:
            Exported conversation string or None if failed
        """
        try:
            conversation = await self.get_conversation(conversation_id)
            
            if not conversation:
                return None
            
            if format.lower() == "json":
                # Export as JSON
                export_data = asdict(conversation)
                return json.dumps(export_data, indent=2, default=str)
            
            elif format.lower() == "txt":
                # Export as plain text
                lines = [f"Conversation: {conversation_id}"]
                lines.append(f"User: {conversation.user_id}")
                lines.append(f"Created: {datetime.fromtimestamp(conversation.created_at)}")
                lines.append(f"Updated: {datetime.fromtimestamp(conversation.updated_at)}")
                lines.append("")
                lines.append("Messages:")
                lines.append("=" * 50)
                
                for message in conversation.messages:
                    timestamp = datetime.fromtimestamp(message.timestamp)
                    lines.append(f"[{timestamp}] {message.role.upper()}: {message.content}")
                
                return "\n".join(lines)
            
            else:
                logger.warning(f"Unsupported export format: {format}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to export conversation: {str(e)}", exc_info=True)
            return None
    
    def __del__(self):
        """Cleanup when memory is destroyed."""
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
