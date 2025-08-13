#!/usr/bin/env python3
"""
Setup script to help configure environment variables for the Healthcare Voice AI Assistant.
This script will create a .env file with the required configuration.
"""

import os
from pathlib import Path

def create_env_file():
    """Create a .env file with required environment variables."""
    
    env_content = """# Healthcare Voice AI Assistant - Environment Configuration
# Fill in your actual API keys below

# Core Application
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# OpenAI Configuration (REQUIRED - Get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=your_openai_api_key_here

# ElevenLabs TTS Configuration (REQUIRED - Get from https://elevenlabs.io/)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# AssemblyAI STT Configuration (Optional - will use OpenAI Whisper if not set)
# ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here

# Pinecone Configuration (Optional - will use local FAISS if not set)
# PINECONE_API_KEY=your_pinecone_api_key_here
# PINECONE_ENVIRONMENT=your_pinecone_environment
# PINECONE_INDEX_NAME=your_pinecone_index_name

# Security (REQUIRED - Generate a random secret key)
SECRET_KEY=your_secret_key_here_make_it_long_and_random

# Other settings will use defaults
"""
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ .env file created successfully!")
        print("\n📝 NEXT STEPS:")
        print("1. Edit the .env file and add your actual API keys:")
        print("   - OPENAI_API_KEY: Get from https://platform.openai.com/api-keys")
        print("   - ELEVENLABS_API_KEY: Get from https://elevenlabs.io/")
        print("   - SECRET_KEY: Generate a random string (at least 32 characters)")
        print("\n2. Save the .env file")
        print("3. Restart your server")
        print("\n🔑 Required API Keys:")
        print("   - OpenAI: For GPT-4 chat and Whisper speech-to-text")
        print("   - ElevenLabs: For high-quality text-to-speech")
        print("   - AssemblyAI: Optional alternative for speech-to-text")
        print("   - Pinecone: Optional for cloud vector storage")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

def check_env_file():
    """Check if .env file exists and show its status."""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Run this script to create it: python setup_env.py")
        return False
    
    print("✅ .env file found!")
    
    # Check required variables
    required_vars = [
        "OPENAI_API_KEY",
        "ELEVENLABS_API_KEY", 
        "SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing required environment variables: {', '.join(missing_vars)}")
        print("Please edit your .env file and add these variables.")
        return False
    else:
        print("✅ All required environment variables are set!")
        return True

if __name__ == "__main__":
    print("🏥 Healthcare Voice AI Assistant - Environment Setup")
    print("=" * 50)
    
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "check":
        check_env_file()
    else:
        create_env_file()
