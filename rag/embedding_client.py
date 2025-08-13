"""
Embedding Client for the Healthcare Voice AI Assistant.
Interfaces with OpenAI's text-embedding-3-large model for generating embeddings.
"""

import time
from typing import List, Optional
import asyncio

import openai
from loguru import logger

from config.settings import get_settings


class EmbeddingClient:
    """Client for generating text embeddings using OpenAI's embedding models."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.openai_embedding_model
        self.rate_limit_delay = 0.1  # Delay between requests to respect rate limits
        
        logger.info(f"Embedding client initialized with model: {self.model}")
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            List of float values representing the embedding vector
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return []
            
            # Truncate text if too long (OpenAI has limits)
            max_tokens = 8000  # Conservative limit for text-embedding-3-large
            if len(text) > max_tokens * 4:  # Rough estimate: 4 chars per token
                text = text[:max_tokens * 4]
                logger.warning(f"Text truncated to {max_tokens * 4} characters for embedding")
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            # Add rate limiting delay
            await asyncio.sleep(self.rate_limit_delay)
            
            logger.debug(f"Generated embedding for text of length {len(text)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}", exc_info=True)
            raise
    
    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for a batch of text strings.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embedding vectors
        """
        try:
            if not texts:
                logger.warning("No texts provided for batch embedding")
                return []
            
            all_embeddings = []
            
            # Process in batches to avoid overwhelming the API
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                logger.debug(f"Processing embedding batch {i//batch_size + 1}: {len(batch)} texts")
                
                batch_embeddings = await self._embed_batch_internal(batch)
                all_embeddings.extend(batch_embeddings)
                
                # Add delay between batches
                if i + batch_size < len(texts):
                    await asyncio.sleep(self.rate_limit_delay * 2)
            
            logger.info(f"Generated embeddings for {len(texts)} texts in {len(all_embeddings)} batches")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}", exc_info=True)
            raise
    
    async def _embed_batch_internal(self, texts: List[str]) -> List[List[float]]:
        """Internal method to process a single batch of texts."""
        try:
            # Filter out empty texts
            valid_texts = [text for text in texts if text and text.strip()]
            
            if not valid_texts:
                return [[] for _ in texts]  # Return empty embeddings for empty texts
            
            # Truncate texts if needed
            max_tokens = 8000
            truncated_texts = []
            for text in valid_texts:
                if len(text) > max_tokens * 4:
                    truncated_texts.append(text[:max_tokens * 4])
                    logger.debug(f"Text truncated for embedding")
                else:
                    truncated_texts.append(text)
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=truncated_texts
            )
            
            embeddings = [data.embedding for data in response.data]
            
            # Pad with empty embeddings for any texts that were filtered out
            result = []
            text_index = 0
            for original_text in texts:
                if original_text and original_text.strip():
                    result.append(embeddings[text_index])
                    text_index += 1
                else:
                    result.append([])
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process embedding batch: {str(e)}", exc_info=True)
            # Return empty embeddings for failed batch
            return [[] for _ in texts]
    
    async def embed_query(self, query: str, query_type: str = "general") -> List[float]:
        """
        Generate embedding for a user query with optional query type context.
        
        Args:
            query: User query text
            query_type: Type of query (e.g., "medical", "general", "symptom")
            
        Returns:
            Query embedding vector
        """
        try:
            # Add query type context if specified
            if query_type and query_type != "general":
                enhanced_query = f"[{query_type.upper()}] {query}"
            else:
                enhanced_query = query
            
            embedding = await self.embed_text(enhanced_query)
            
            logger.debug(f"Generated query embedding for type: {query_type}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {str(e)}", exc_info=True)
            raise
    
    async def get_embedding_dimensions(self) -> int:
        """
        Get the dimensionality of the embedding model.
        
        Returns:
            Number of dimensions in the embedding vectors
        """
        try:
            # Generate a simple test embedding to get dimensions
            test_text = "test"
            embedding = await self.embed_text(test_text)
            dimensions = len(embedding)
            
            logger.debug(f"Embedding model dimensions: {dimensions}")
            return dimensions
            
        except Exception as e:
            logger.error(f"Failed to get embedding dimensions: {str(e)}", exc_info=True)
            # Return default dimension for text-embedding-3-large
            return 1536
    
    async def health_check(self) -> bool:
        """
        Perform health check on the embedding client.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Test with a simple embedding
            test_text = "health check"
            embedding = await self.embed_text(test_text)
            
            if not embedding or len(embedding) == 0:
                return False
            
            # Check if dimensions match expected
            expected_dimensions = 1536  # text-embedding-3-large
            if len(embedding) != expected_dimensions:
                logger.warning(f"Unexpected embedding dimensions: {len(embedding)} vs {expected_dimensions}")
                return False
            
            logger.debug("Embedding client health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Embedding client health check failed: {str(e)}", exc_info=True)
            return False
    
    async def get_usage_stats(self) -> dict:
        """
        Get usage statistics for the embedding client.
        
        Returns:
            Dictionary with usage information
        """
        try:
            # This would typically come from OpenAI's usage API
            # For now, return basic information
            stats = {
                "model": self.model,
                "dimensions": await self.get_embedding_dimensions(),
                "rate_limit_delay": self.rate_limit_delay,
                "status": "active"
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def set_rate_limit_delay(self, delay: float):
        """
        Set the delay between API requests for rate limiting.
        
        Args:
            delay: Delay in seconds
        """
        self.rate_limit_delay = max(0.01, delay)  # Minimum 10ms delay
        logger.info(f"Rate limit delay set to {self.rate_limit_delay}s")
    
    async def close(self):
        """Close the embedding client and cleanup resources."""
        try:
            # Close OpenAI client
            await self.client.close()
            logger.info("Embedding client closed")
        except Exception as e:
            logger.warning(f"Error closing embedding client: {str(e)}")
