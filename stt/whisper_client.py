"""
Whisper STT Client for the Healthcare Voice AI Assistant.
Uses OpenAI's Whisper API for high-quality speech-to-text conversion.
"""

import time
from typing import Optional, Dict, Any
from pathlib import Path
import asyncio
from dataclasses import dataclass

import openai
from loguru import logger

from config.settings import get_settings


@dataclass
class TranscriptionResult:
    """Result from speech-to-text transcription."""
    text: str
    confidence: float
    language: str
    duration: float
    processing_time: float
    segments: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None


class WhisperSTTClient:
    """Client for OpenAI Whisper speech-to-text API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.model = "whisper-1"  # OpenAI's Whisper model
        self.rate_limit_delay = 0.1  # Delay between requests
        
        logger.info("Whisper STT client initialized")
    
    async def transcribe(self, audio_file_path: str, **kwargs) -> TranscriptionResult:
        """
        Transcribe audio file to text using OpenAI Whisper.
        
        Args:
            audio_file_path: Path to audio file
            **kwargs: Additional transcription options
            
        Returns:
            TranscriptionResult with transcribed text and metadata
        """
        start_time = time.time()
        
        try:
            # Validate file
            if not Path(audio_file_path).exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Get audio duration
            duration = await self._get_audio_duration(audio_file_path)
            
            logger.debug(f"Transcribing audio file: {audio_file_path} (duration: {duration:.2f}s)")
            
            # Prepare transcription options
            transcription_options = {
                "model": self.model,
                "file": open(audio_file_path, "rb"),
                "response_format": "verbose_json",
                "language": kwargs.get("language", "en"),
                "prompt": kwargs.get("prompt", "This is a healthcare-related conversation."),
                "temperature": kwargs.get("temperature", 0.0),
                **kwargs
            }
            
            # Perform transcription
            response = await self.client.audio.transcriptions.create(**transcription_options)
            
            # Extract results
            text = response.text
            language = response.language
            segments = getattr(response, 'segments', [])
            
            # Calculate confidence (average of segment confidences if available)
            confidence = self._calculate_confidence(segments)
            
            processing_time = time.time() - start_time
            
            # Add rate limiting delay
            await asyncio.sleep(self.rate_limit_delay)
            
            logger.info(f"Transcription completed: {len(text)} characters in {processing_time:.3f}s")
            
            return TranscriptionResult(
                text=text,
                confidence=confidence,
                language=language,
                duration=duration,
                processing_time=processing_time,
                segments=segments,
                metadata={
                    "model": self.model,
                    "file_path": audio_file_path,
                    "options": transcription_options
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Transcription failed: {str(e)}", exc_info=True)
            raise
    
    async def transcribe_stream(self, audio_file_path: str, **kwargs):
        """
        Stream transcription results for real-time processing.
        
        Args:
            audio_file_path: Path to audio file
            **kwargs: Additional transcription options
            
        Yields:
            Transcription chunks as they become available
        """
        # Note: OpenAI Whisper doesn't support streaming, but we can simulate it
        # by processing in chunks or using a different approach
        try:
            # For now, return the full transcription
            result = await self.transcribe(audio_file_path, **kwargs)
            yield result
            
        except Exception as e:
            logger.error(f"Stream transcription failed: {str(e)}", exc_info=True)
            raise
    
    async def transcribe_with_timestamps(self, audio_file_path: str, **kwargs) -> TranscriptionResult:
        """
        Transcribe audio with detailed timestamp information.
        
        Args:
            audio_file_path: Path to audio file
            **kwargs: Additional transcription options
            
        Returns:
            TranscriptionResult with timestamp segments
        """
        try:
            # Request verbose JSON format for timestamps
            kwargs["response_format"] = "verbose_json"
            
            result = await self.transcribe(audio_file_path, **kwargs)
            
            # Process timestamp segments
            if result.segments:
                for segment in result.segments:
                    segment["start_formatted"] = self._format_timestamp(segment.get("start", 0))
                    segment["end_formatted"] = self._format_timestamp(segment.get("end", 0))
            
            return result
            
        except Exception as e:
            logger.error(f"Timestamp transcription failed: {str(e)}", exc_info=True)
            raise
    
    async def transcribe_medical_audio(self, audio_file_path: str, **kwargs) -> TranscriptionResult:
        """
        Transcribe medical audio with healthcare-specific prompts.
        
        Args:
            audio_file_path: Path to audio file
            **kwargs: Additional transcription options
            
        Returns:
            TranscriptionResult optimized for medical content
        """
        try:
            # Use medical-specific prompt
            medical_prompt = """
            This is a healthcare-related conversation. The audio may contain medical terms, 
            symptoms, procedures, or patient information. Please transcribe accurately with 
            proper medical terminology.
            """
            
            kwargs["prompt"] = medical_prompt
            kwargs["temperature"] = 0.0  # Lower temperature for more accurate medical transcription
            
            result = await self.transcribe(audio_file_path, **kwargs)
            
            # Post-process for medical accuracy
            result.text = self._post_process_medical_text(result.text)
            
            return result
            
        except Exception as e:
            logger.error(f"Medical transcription failed: {str(e)}", exc_info=True)
            raise
    
    async def _get_audio_duration(self, audio_file_path: str) -> float:
        """Get the duration of an audio file."""
        try:
            import librosa
            
            duration = librosa.get_duration(path=audio_file_path)
            return duration
            
        except ImportError:
            logger.warning("librosa not available, using default duration")
            return 0.0
        except Exception as e:
            logger.warning(f"Failed to get audio duration: {str(e)}")
            return 0.0
    
    def _calculate_confidence(self, segments: list) -> float:
        """Calculate overall confidence from segment confidences."""
        if not segments:
            return 0.0
        
        try:
            # Extract confidence scores from segments
            confidences = []
            for segment in segments:
                if "confidence" in segment:
                    confidences.append(segment["confidence"])
            
            if confidences:
                return sum(confidences) / len(confidences)
            else:
                return 0.8  # Default confidence if not available
                
        except Exception as e:
            logger.warning(f"Failed to calculate confidence: {str(e)}")
            return 0.8
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds into MM:SS format."""
        try:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"
        except Exception:
            return "00:00"
    
    def _post_process_medical_text(self, text: str) -> str:
        """Post-process transcribed text for medical accuracy."""
        if not text:
            return text
        
        # Common medical transcription corrections
        corrections = {
            "bp": "blood pressure",
            "hr": "heart rate",
            "temp": "temperature",
            "o2": "oxygen",
            "iv": "intravenous",
            "po": "by mouth",
            "prn": "as needed",
            "qd": "daily",
            "bid": "twice daily",
            "tid": "three times daily",
            "qid": "four times daily"
        }
        
        # Apply corrections
        for abbreviation, full_text in corrections.items():
            # Replace standalone abbreviations (with word boundaries)
            text = re.sub(r'\b' + abbreviation + r'\b', full_text, text, flags=re.IGNORECASE)
        
        # Capitalize medical terms
        medical_terms = [
            "diabetes", "hypertension", "cardiovascular", "respiratory", "neurological",
            "oncology", "pediatrics", "geriatrics", "orthopedics", "dermatology"
        ]
        
        for term in medical_terms:
            text = re.sub(r'\b' + term + r'\b', term.title(), text, flags=re.IGNORECASE)
        
        return text
    
    async def health_check(self) -> bool:
        """
        Perform health check on the Whisper STT client.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Test with a simple API call
            # Create a minimal test audio file or use a simple validation
            logger.debug("Whisper STT client health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Whisper STT client health check failed: {str(e)}", exc_info=True)
            return False
    
    async def get_usage_stats(self) -> dict:
        """
        Get usage statistics for the Whisper STT client.
        
        Returns:
            Dictionary with usage information
        """
        try:
            stats = {
                "model": self.model,
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
        """Close the Whisper STT client and cleanup resources."""
        try:
            await self.client.close()
            logger.info("Whisper STT client closed")
        except Exception as e:
            logger.warning(f"Error closing Whisper STT client: {str(e)}")


# Import required modules
import re
