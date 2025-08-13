"""
Voice API routes for the Healthcare Voice AI Assistant.
Handles speech-to-text and text-to-speech operations.
"""

import time
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import aiofiles

from stt.whisper_client import WhisperSTTClient
from tts.elevenlabs_client import ElevenLabsTTSClient
from utils.logger import logger, log_voice_processing
from config.settings import get_settings

router = APIRouter()

# Initialize clients
stt_client = WhisperSTTClient()
tts_client = ElevenLabsTTSClient()


class TTSRequest(BaseModel):
    """Request model for text-to-speech."""
    text: str
    voice_id: Optional[str] = None
    speed: Optional[float] = 1.0
    stability: Optional[float] = 0.5
    clarity: Optional[float] = 0.75


class TranscriptionResponse(BaseModel):
    """Response model for speech-to-text."""
    text: str
    confidence: float
    language: str
    duration: float
    processing_time: float


class TTSResponse(BaseModel):
    """Response model for text-to-speech."""
    audio_url: str
    duration: float
    processing_time: float
    voice_id: str


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...)
):
    """
    Transcribe uploaded audio file to text.
    
    Args:
        audio_file: Audio file to transcribe (WAV, MP3, M4A, FLAC)
        background_tasks: Background tasks for cleanup
    
    Returns:
        TranscriptionResponse with transcribed text and metadata
    """
    start_time = time.time()
    settings = get_settings()
    
    # Validate file type
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = Path(audio_file.filename).suffix.lower().lstrip('.')
    if file_ext not in settings.allowed_audio_formats:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported audio format. Supported: {settings.allowed_audio_formats}"
        )
    
    # Validate file size
    if audio_file.size and audio_file.size > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.max_file_size / 1024 / 1024:.1f}MB"
        )
    
    try:
        # Save uploaded file temporarily
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(exist_ok=True)
        
        temp_file_path = upload_dir / f"temp_{int(start_time)}_{audio_file.filename}"
        
        async with aiofiles.open(temp_file_path, 'wb') as f:
            content = await audio_file.read()
            await f.write(content)
        
        # Get audio duration (approximate)
        import librosa
        try:
            audio_info = librosa.get_duration(path=str(temp_file_path))
        except Exception:
            audio_info = 0.0
        
        # Transcribe audio
        transcription_result = await stt_client.transcribe(str(temp_file_path))
        
        processing_time = time.time() - start_time
        
        # Log successful transcription
        log_voice_processing(
            audio_format=file_ext,
            duration_seconds=audio_info,
            processing_type="transcription",
            success=True
        )
        
        # Cleanup temp file in background
        background_tasks.add_task(cleanup_temp_file, temp_file_path)
        
        return TranscriptionResponse(
            text=transcription_result.text,
            confidence=transcription_result.confidence,
            language=transcription_result.language,
            duration=audio_info,
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        # Log failed transcription
        log_voice_processing(
            audio_format=file_ext,
            duration_seconds=0.0,
            processing_type="transcription",
            success=False,
            error=str(e)
        )
        
        logger.error(f"Transcription failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """
    Convert text to speech using ElevenLabs TTS.
    
    Args:
        request: TTSRequest with text and voice parameters
        
    Returns:
        TTSResponse with audio URL and metadata
    """
    start_time = time.time()
    settings = get_settings()
    
    try:
        # Validate text length
        if len(request.text) > settings.max_response_length:
            raise HTTPException(
                status_code=400,
                detail=f"Text too long. Max length: {settings.max_response_length} characters"
            )
        
        # Use default voice if not specified
        voice_id = request.voice_id or settings.elevenlabs_voice_id
        
        # Synthesize speech
        audio_data = await tts_client.synthesize(
            text=request.text,
            voice_id=voice_id,
            speed=request.speed,
            stability=request.stability,
            clarity=request.clarity
        )
        
        # Save audio file
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(exist_ok=True)
        
        audio_filename = f"tts_{int(start_time)}.mp3"
        audio_path = upload_dir / audio_filename
        
        async with aiofiles.open(audio_path, 'wb') as f:
            await f.write(audio_data)
        
        processing_time = time.time() - start_time
        
        # Get audio duration
        import librosa
        try:
            duration = librosa.get_duration(path=str(audio_path))
        except Exception:
            duration = 0.0
        
        # Log successful synthesis
        log_voice_processing(
            audio_format="mp3",
            duration_seconds=duration,
            processing_type="synthesis",
            success=True
        )
        
        return TTSResponse(
            audio_url=f"/uploads/{audio_filename}",
            duration=duration,
            processing_time=processing_time,
            voice_id=voice_id
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        # Log failed synthesis
        log_voice_processing(
            audio_format="mp3",
            duration_seconds=0.0,
            processing_type="synthesis",
            success=False,
            error=str(e)
        )
        
        logger.error(f"Speech synthesis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")


@router.post("/stream-transcribe")
async def stream_transcribe_audio(audio_file: UploadFile = File(...)):
    """
    Stream transcription results for real-time processing.
    
    Args:
        audio_file: Audio file to transcribe
        
    Returns:
        Streaming response with transcription chunks
    """
    # This would implement streaming transcription
    # For now, return a placeholder
    raise HTTPException(status_code=501, detail="Streaming transcription not yet implemented")


@router.get("/voices")
async def list_available_voices():
    """
    List available TTS voices.
    
    Returns:
        List of available voice options
    """
    try:
        voices = await tts_client.list_voices()
        return {"voices": voices}
    except Exception as e:
        logger.error(f"Failed to list voices: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list voices")


async def cleanup_temp_file(file_path: Path):
    """Clean up temporary files."""
    try:
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"Cleaned up temp file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {file_path}: {str(e)}")


@router.get("/health")
async def voice_health_check():
    """Health check for voice processing services."""
    try:
        # Check STT service
        stt_healthy = await stt_client.health_check()
        
        # Check TTS service
        tts_healthy = await tts_client.health_check()
        
        return {
            "status": "healthy" if stt_healthy and tts_healthy else "degraded",
            "stt_service": "healthy" if stt_healthy else "unhealthy",
            "tts_service": "healthy" if tts_healthy else "unhealthy",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Voice health check failed: {str(e)}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }
