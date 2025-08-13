"""
Configuration settings for the Healthcare Voice AI Assistant.
Handles environment variables and provides typed configuration.
"""

import os
from typing import List, Optional

try:
    # Try pydantic-settings first (Pydantic v2)
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    try:
        # Fallback to pydantic v1
        from pydantic import BaseSettings, Field
    except ImportError:
        # If neither works, install pydantic-settings
        raise ImportError(
            "Please install pydantic-settings: pip install pydantic-settings"
        )


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Core Application
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-large", env="OPENAI_EMBEDDING_MODEL")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.1, env="OPENAI_TEMPERATURE")
    
    # ElevenLabs TTS Configuration
    elevenlabs_api_key: str = Field(..., env="ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str = Field(default="21m00Tcm4TlvDq8ikWAM", env="ELEVENLABS_VOICE_ID")
    elevenlabs_model_id: str = Field(default="eleven_monolingual_v1", env="ELEVENLABS_MODEL_ID")
    
    # AssemblyAI STT Configuration
    assemblyai_api_key: Optional[str] = Field(default=None, env="ASSEMBLYAI_API_KEY")
    assemblyai_language_code: str = Field(default="en", env="ASSEMBLYAI_LANGUAGE_CODE")
    
    # Pinecone Configuration
    pinecone_api_key: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(default=None, env="PINECONE_ENVIRONMENT")
    pinecone_index_name: Optional[str] = Field(default=None, env="PINECONE_INDEX_NAME")
    
    # RAG Configuration
    embedding_model: str = Field(default="text-embedding-3-large", env="EMBEDDING_MODEL")
    top_k_results: int = Field(default=5, env="TOP_K_RESULTS")
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    
    # Voice Processing
    sample_rate: int = Field(default=16000, env="SAMPLE_RATE")
    chunk_duration_ms: int = Field(default=1000, env="CHUNK_DURATION_MS")
    max_recording_time: int = Field(default=30, env="MAX_RECORDING_TIME")
    vad_mode: int = Field(default=3, env="VAD_MODE")
    vad_frame_duration: int = Field(default=30, env="VAD_FRAME_DURATION")
    
    # Memory and Context
    max_conversation_history: int = Field(default=10, env="MAX_CONVERSATION_HISTORY")
    memory_ttl_hours: int = Field(default=24, env="MEMORY_TTL_HOURS")
    enable_long_term_memory: bool = Field(default=False, env="ENABLE_LONG_TERM_MEMORY")
    
    # Safety and Compliance
    healthcare_disclaimer: bool = Field(default=True, env="HEALTHCARE_DISCLAIMER")
    block_medical_advice: bool = Field(default=True, env="BLOCK_MEDICAL_ADVICE")
    require_disclaimer: bool = Field(default=True, env="REQUIRE_DISCLAIMER")
    max_response_length: int = Field(default=500, env="MAX_RESPONSE_LENGTH")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000"], env="CORS_ORIGINS")
    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    max_requests_per_minute: int = Field(default=60, env="MAX_REQUESTS_PER_MINUTE")
    
    # Monitoring and Logging
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # File Storage
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    allowed_audio_formats: List[str] = Field(default=["wav", "mp3", "m4a", "flac"], env="ALLOWED_AUDIO_FORMATS")
    
    # Development
    reload: bool = Field(default=True, env="RELOAD")
    workers: int = Field(default=1, env="WORKERS")
    enable_debug_endpoints: bool = Field(default=True, env="ENABLE_DEBUG_ENDPOINTS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def is_production() -> bool:
    """Check if running in production environment."""
    return settings.environment.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    return settings.environment.lower() == "development"
