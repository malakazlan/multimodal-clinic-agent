"""
OpenAI LLM Client for the Healthcare Voice AI Assistant.
Generates AI responses with context grounding and hallucination reduction.
"""

import time
from typing import List, Dict, Any, Optional
import asyncio
from dataclasses import dataclass

import openai
from loguru import logger

from config.settings import get_settings


@dataclass
class LLMResponse:
    """Response from LLM generation."""
    content: str
    tokens_used: int
    processing_time: float
    model: str
    metadata: Optional[Dict[str, Any]] = None


class OpenAILLMClient:
    """Client for OpenAI LLM API with healthcare-specific optimizations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.openai_model
        self.max_tokens = self.settings.openai_max_tokens
        self.temperature = self.settings.openai_temperature
        self.rate_limit_delay = 0.1  # Delay between requests
        
        logger.info(f"OpenAI LLM client initialized with model: {self.model}")
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = None,
        temperature: float = None,
        **kwargs
    ) -> str:
        """
        Generate AI response using OpenAI LLM.
        
        Args:
            messages: List of message dictionaries with role and content
            max_tokens: Maximum tokens for response
            temperature: Response creativity (0.0 to 2.0)
            **kwargs: Additional generation options
            
        Returns:
            Generated response text
        """
        try:
            # Use settings defaults if not provided
            max_tokens = max_tokens or self.max_tokens
            temperature = temperature or self.temperature
            
            # Validate messages
            if not messages or len(messages) == 0:
                raise ValueError("No messages provided for LLM generation")
            
            logger.debug(f"Generating LLM response with {len(messages)} messages")
            
            # Prepare generation options
            generation_options = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                **kwargs
            }
            
            # Generate response
            response = await self.client.chat.completions.create(**generation_options)
            
            # Extract response content
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
            else:
                raise Exception("No response content generated")
            
            # Add rate limiting delay
            await asyncio.sleep(self.rate_limit_delay)
            
            logger.debug(f"LLM response generated: {len(content)} characters")
            return content
            
        except Exception as e:
            logger.error(f"LLM response generation failed: {str(e)}", exc_info=True)
            raise
    
    async def generate_response_with_metadata(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = None,
        temperature: float = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate AI response with detailed metadata.
        
        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens for response
            temperature: Response creativity
            **kwargs: Additional generation options
            
        Returns:
            LLMResponse with content and metadata
        """
        start_time = time.time()
        
        try:
            # Generate response
            content = await self.generate_response(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            processing_time = time.time() - start_time
            
            # Create response object
            response = LLMResponse(
                content=content,
                tokens_used=len(content.split()),  # Rough token estimation
                processing_time=processing_time,
                model=self.model,
                metadata={
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages_count": len(messages),
                    "generation_options": kwargs
                }
            )
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"LLM response generation with metadata failed: {str(e)}", exc_info=True)
            raise
    
    async def generate_healthcare_response(
        self,
        messages: List[Dict[str, str]],
        context_sources: List[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Generate healthcare-specific AI response with safety measures.
        
        Args:
            messages: List of message dictionaries
            context_sources: RAG context sources
            **kwargs: Additional generation options
            
        Returns:
            Healthcare-optimized response
        """
        try:
            # Enhance system message for healthcare
            enhanced_messages = self._enhance_healthcare_context(messages, context_sources)
            
            # Use healthcare-optimized settings
            healthcare_options = {
                "temperature": 0.1,  # Lower temperature for more factual responses
                "max_tokens": self.max_tokens,
                "top_p": 0.9,  # Slightly more focused
                "frequency_penalty": 0.1,  # Reduce repetition
                "presence_penalty": 0.1,  # Encourage diverse responses
                **kwargs
            }
            
            # Generate response
            response = await self.generate_response(
                messages=enhanced_messages,
                **healthcare_options
            )
            
            # Post-process for healthcare safety
            processed_response = self._post_process_healthcare_response(response)
            
            return processed_response
            
        except Exception as e:
            logger.error(f"Healthcare response generation failed: {str(e)}", exc_info=True)
            raise
    
    def _enhance_healthcare_context(
        self,
        messages: List[Dict[str, str]],
        context_sources: List[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Enhance messages with healthcare-specific context and safety instructions."""
        enhanced_messages = []
        
        # Add or enhance system message
        system_message = None
        for message in messages:
            if message["role"] == "system":
                system_message = message
                break
        
        if not system_message:
            system_message = {"role": "system", "content": ""}
        
        # Enhance system message with healthcare safety
        healthcare_safety = """
IMPORTANT HEALTHCARE SAFETY RULES:
1. NEVER provide medical advice, diagnosis, or treatment recommendations
2. ALWAYS encourage users to consult healthcare professionals for medical concerns
3. Focus on providing educational information and general guidance
4. If asked about symptoms, treatments, or medical procedures, refer to healthcare providers
5. Be clear about the limitations of your knowledge and the importance of professional medical consultation
6. Use language that is clear, compassionate, and non-alarming
7. Emphasize the importance of seeking professional medical help when appropriate

Your role is to provide helpful, accurate healthcare information while following all safety guidelines.
"""
        
        # Add context sources if available
        if context_sources:
            context_text = "\n\nAVAILABLE HEALTHCARE INFORMATION SOURCES:\n"
            for i, source in enumerate(context_sources[:3]):  # Limit to top 3 sources
                context_text += f"{i+1}. {source.get('title', 'Unknown')} "
                context_text += f"(Source: {source.get('source', 'Unknown')})\n"
                context_text += f"   Relevance: {source.get('relevance_score', 0):.2f}\n"
                context_text += f"   Content: {source.get('snippet', '')[:200]}...\n\n"
            
            system_message["content"] = healthcare_safety + context_text
        else:
            system_message["content"] = healthcare_safety
        
        enhanced_messages.append(system_message)
        
        # Add other messages
        for message in messages:
            if message["role"] != "system":
                enhanced_messages.append(message)
        
        return enhanced_messages
    
    def _post_process_healthcare_response(self, response: str) -> str:
        """Post-process response for healthcare safety and clarity."""
        if not response:
            return response
        
        # Add safety disclaimer if not present
        safety_keywords = [
            "disclaimer", "medical advice", "consult", "professional", "healthcare provider"
        ]
        
        has_safety_content = any(keyword.lower() in response.lower() for keyword in safety_keywords)
        
        if not has_safety_content:
            response += "\n\n⚠️ IMPORTANT: This information is for educational purposes only. "
            response += "Always consult with qualified healthcare professionals for medical concerns, "
            response += "diagnosis, and treatment."
        
        # Ensure response doesn't exceed maximum length
        max_length = self.settings.max_response_length
        if len(response) > max_length:
            response = response[:max_length-3] + "..."
        
        return response
    
    async def generate_streaming_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = None,
        temperature: float = None,
        **kwargs
    ):
        """
        Generate streaming AI response for real-time output.
        
        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens for response
            temperature: Response creativity
            **kwargs: Additional generation options
            
        Yields:
            Response chunks as they become available
        """
        try:
            # Use settings defaults if not provided
            max_tokens = max_tokens or self.max_tokens
            temperature = temperature or self.temperature
            
            # Prepare generation options
            generation_options = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
                **kwargs
            }
            
            # Generate streaming response
            stream = await self.client.chat.completions.create(**generation_options)
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming LLM response generation failed: {str(e)}", exc_info=True)
            raise
    
    async def generate_fallback_response(self, user_message: str) -> str:
        """
        Generate a safe fallback response when main generation fails.
        
        Args:
            user_message: User's original message
            
        Returns:
            Safe fallback response
        """
        try:
            fallback_messages = [
                {
                    "role": "system",
                    "content": "You are a healthcare information assistant. Provide a brief, helpful response that encourages the user to consult healthcare professionals."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
            
            response = await self.generate_response(
                messages=fallback_messages,
                max_tokens=100,  # Shorter response
                temperature=0.1   # More conservative
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Fallback response generation failed: {str(e)}", exc_info=True)
            # Return hardcoded fallback
            return ("I apologize, but I'm unable to provide a response at the moment. "
                   "Please consult with a healthcare professional for your medical concerns.")
    
    async def health_check(self) -> bool:
        """
        Perform health check on the OpenAI LLM client.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Test with a simple generation
            test_messages = [
                {"role": "user", "content": "Hello, this is a health check."}
            ]
            
            response = await self.generate_response(
                messages=test_messages,
                max_tokens=10,
                temperature=0.0
            )
            
            if response and len(response) > 0:
                logger.debug("OpenAI LLM client health check passed")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"OpenAI LLM client health check failed: {str(e)}", exc_info=True)
            return False
    
    async def get_usage_stats(self) -> dict:
        """
        Get usage statistics for the OpenAI LLM client.
        
        Returns:
            Dictionary with usage information
        """
        try:
            stats = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "rate_limit_delay": self.rate_limit_delay,
                "status": "active",
                "provider": "openai"
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
        self.rate_limit_delay = max(0.01, delay)
        logger.info(f"Rate limit delay set to {self.rate_limit_delay}s")
    
    async def close(self):
        """Close the OpenAI LLM client and cleanup resources."""
        try:
            await self.client.close()
            logger.info("OpenAI LLM client closed")
        except Exception as e:
            logger.warning(f"Error closing OpenAI LLM client: {str(e)}")
