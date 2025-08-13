"""
ElevenLabs TTS Client for the Healthcare Voice AI Assistant.
Uses ElevenLabs API for high-quality text-to-speech conversion.
"""

import time
from typing import List, Optional, Dict, Any
import asyncio
import aiohttp
from dataclasses import dataclass

from loguru import logger

from config.settings import get_settings


@dataclass
class VoiceInfo:
    """Information about an ElevenLabs voice."""
    voice_id: str
    name: str
    category: str
    description: str
    labels: Dict[str, str]
    preview_url: Optional[str] = None


@dataclass
class TTSResult:
    """Result from text-to-speech conversion."""
    audio_data: bytes
    duration: float
    processing_time: float
    voice_id: str
    metadata: Optional[Dict[str, Any]] = None


class ElevenLabsTTSClient:
    """Client for ElevenLabs text-to-speech API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.elevenlabs_api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        self.default_voice_id = self.settings.elevenlabs_voice_id
        self.default_model_id = self.settings.elevenlabs_model_id
        self.rate_limit_delay = 0.1  # Delay between requests
        
        # HTTP session for API calls
        self.session = None
        
        logger.info("ElevenLabs TTS client initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json"
                }
            )
        return self.session
    
    async def synthesize(
        self,
        text: str,
        voice_id: str = None,
        speed: float = 1.0,
        stability: float = 0.5,
        clarity: float = 0.75,
        **kwargs
    ) -> bytes:
        """
        Convert text to speech using ElevenLabs TTS.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use (defaults to configured voice)
            speed: Speech speed (0.25 to 4.0)
            stability: Voice stability (0 to 1.0)
            clarity: Voice clarity (0 to 1.0)
            **kwargs: Additional TTS options
            
        Returns:
            Audio data as bytes
        """
        start_time = time.time()
        
        try:
            if not text or not text.strip():
                raise ValueError("No text provided for TTS")
            
            # Use default voice if not specified
            voice_id = voice_id or self.default_voice_id
            
            # Validate parameters
            speed = max(0.25, min(4.0, speed))
            stability = max(0.0, min(1.0, stability))
            clarity = max(0.0, min(1.0, clarity))
            
            logger.debug(f"Synthesizing text: '{text[:50]}...' with voice {voice_id}")
            
            # Prepare request payload
            payload = {
                "text": text,
                "model_id": self.default_model_id,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": clarity,
                    "style": 0.0,
                    "use_speaker_boost": True
                },
                "optimization_level": 0
            }
            
            # Add speed if not default
            if speed != 1.0:
                payload["voice_settings"]["speed"] = speed
            
            # Add additional options
            payload.update(kwargs)
            
            # Make API request
            session = await self._get_session()
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"TTS API error: {response.status} - {error_text}")
                
                audio_data = await response.read()
            
            # Add rate limiting delay
            await asyncio.sleep(self.rate_limit_delay)
            
            processing_time = time.time() - start_time
            logger.info(f"TTS synthesis completed: {len(audio_data)} bytes in {processing_time:.3f}s")
            
            return audio_data
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"TTS synthesis failed: {str(e)}", exc_info=True)
            raise
    
    async def synthesize_stream(
        self,
        text: str,
        voice_id: str = None,
        **kwargs
    ):
        """
        Stream TTS synthesis results for real-time processing.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use
            **kwargs: Additional TTS options
            
        Yields:
            Audio chunks as they become available
        """
        try:
            # For now, return the full audio data
            # ElevenLabs supports streaming, but this is a simplified implementation
            audio_data = await self.synthesize(text, voice_id, **kwargs)
            yield audio_data
            
        except Exception as e:
            logger.error(f"Stream TTS synthesis failed: {str(e)}", exc_info=True)
            raise
    
    async def list_voices(self) -> List[VoiceInfo]:
        """
        Get list of available voices.
        
        Returns:
            List of VoiceInfo objects
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/voices"
            
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Voices API error: {response.status} - {error_text}")
                
                data = await response.json()
            
            voices = []
            for voice_data in data.get("voices", []):
                voice = VoiceInfo(
                    voice_id=voice_data["voice_id"],
                    name=voice_data["name"],
                    category=voice_data.get("category", "unknown"),
                    description=voice_data.get("description", ""),
                    labels=voice_data.get("labels", {}),
                    preview_url=voice_data.get("preview_url")
                )
                voices.append(voice)
            
            logger.debug(f"Retrieved {len(voices)} available voices")
            return voices
            
        except Exception as e:
            logger.error(f"Failed to list voices: {str(e)}", exc_info=True)
            return []
    
    async def get_voice_info(self, voice_id: str) -> Optional[VoiceInfo]:
        """
        Get information about a specific voice.
        
        Args:
            voice_id: ID of the voice to retrieve
            
        Returns:
            VoiceInfo object or None if not found
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/voices/{voice_id}"
            
            async with session.get(url) as response:
                if response.status != 200:
                    if response.status == 404:
                        return None
                    error_text = await response.text()
                    raise Exception(f"Voice API error: {response.status} - {error_text}")
                
                voice_data = await response.json()
            
            voice = VoiceInfo(
                voice_id=voice_data["voice_id"],
                name=voice_data["name"],
                category=voice_data.get("category", "unknown"),
                description=voice_data.get("description", ""),
                labels=voice_data.get("labels", {}),
                preview_url=voice_data.get("preview_url")
            )
            
            return voice
            
        except Exception as e:
            logger.error(f"Failed to get voice info for {voice_id}: {str(e)}", exc_info=True)
            return None
    
    async def synthesize_medical_text(
        self,
        text: str,
        voice_id: str = None,
        **kwargs
    ) -> bytes:
        """
        Synthesize medical text with healthcare-optimized voice settings.
        
        Args:
            text: Medical text to convert to speech
            voice_id: Voice ID to use
            **kwargs: Additional TTS options
            
        Returns:
            Audio data as bytes
        """
        try:
            # Use healthcare-optimized settings
            medical_settings = {
                "stability": 0.8,  # Higher stability for medical content
                "clarity": 0.9,    # Higher clarity for medical terms
                "speed": 0.9,      # Slightly slower for comprehension
                **kwargs
            }
            
            # Preprocess medical text
            processed_text = self._preprocess_medical_text(text)
            
            audio_data = await self.synthesize(
                text=processed_text,
                voice_id=voice_id,
                **medical_settings
            )
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Medical TTS synthesis failed: {str(e)}", exc_info=True)
            raise
    
    def _preprocess_medical_text(self, text: str) -> str:
        """Preprocess medical text for better TTS pronunciation."""
        if not text:
            return text
        
        # Common medical pronunciation corrections
        corrections = {
            "mg": "milligrams",
            "ml": "milliliters",
            "kg": "kilograms",
            "cm": "centimeters",
            "mm": "millimeters",
            "hr": "hours",
            "min": "minutes",
            "sec": "seconds",
            "BP": "blood pressure",
            "HR": "heart rate",
            "O2": "oxygen",
            "IV": "intravenous"
        }
        
        # Apply corrections
        for abbreviation, full_text in corrections.items():
            # Replace standalone abbreviations (with word boundaries)
            text = re.sub(r'\b' + abbreviation + r'\b', full_text, text, flags=re.IGNORECASE)
        
        # Add pauses for better comprehension
        text = re.sub(r'([.!?])\s+', r'\1 ... ', text)
        
        return text
    
    async def health_check(self) -> bool:
        """
        Perform health check on the ElevenLabs TTS client.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Test API connectivity with a simple request
            session = await self._get_session()
            url = f"{self.base_url}/voices"
            
            async with session.get(url) as response:
                if response.status == 200:
                    logger.debug("ElevenLabs TTS client health check passed")
                    return True
                else:
                    logger.warning(f"ElevenLabs API returned status {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"ElevenLabs TTS client health check failed: {str(e)}", exc_info=True)
            return False
    
    async def get_usage_stats(self) -> dict:
        """
        Get usage statistics for the ElevenLabs TTS client.
        
        Returns:
            Dictionary with usage information
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/user"
            
            async with session.get(url) as response:
                if response.status == 200:
                    user_data = await response.json()
                    
                    stats = {
                        "subscription_tier": user_data.get("subscription", {}).get("tier", "unknown"),
                        "character_count": user_data.get("subscription", {}).get("character_count", 0),
                        "character_limit": user_data.get("subscription", {}).get("character_limit", 0),
                        "can_extend_character_limit": user_data.get("subscription", {}).get("can_extend_character_limit", False),
                        "status": "active"
                    }
                    
                    return stats
                else:
                    return {"status": "error", "error": f"API returned status {response.status}"}
                    
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
        """Close the ElevenLabs TTS client and cleanup resources."""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
            logger.info("ElevenLabs TTS client closed")
        except Exception as e:
            logger.warning(f"Error closing ElevenLabs TTS client: {str(e)}")


# Import required modules
import re
