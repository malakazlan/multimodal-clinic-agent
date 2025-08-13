
<img width="1128" height="877" alt="main" src="https://github.com/user-attachments/assets/6c7cbae4-ae74-4fb3-a045-044077b857dc" />


<img width="1230" height="827" alt="main2" src="https://github.com/user-attachments/assets/cdeba7ce-0c3b-4410-92dd-f4b183f37919" />


<img width="1092" height="555" alt="work1" src="https://github.com/user-attachments/assets/4ac9e46a-e452-446d-8947-45bf3361ba6e" />

<img width="1422" height="852" alt="2" src="https://github.com/user-attachments/assets/351c595f-30a5-47bc-a0f8-09358e36af04" />





# Healthcare Voice AI Assistant

> **Enterprise-Grade RAG System with Advanced Voice Capabilities**

A production-ready Retrieval-Augmented Generation (RAG) platform designed for healthcare applications, featuring real-time voice interaction, advanced AI models, and enterprise-grade security. This system provides intelligent healthcare knowledge retrieval through natural language processing and voice synthesis.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Usage Guide](#usage-guide)
- [Development](#development)
- [Deployment](#deployment)
- [Security & Compliance](#security--compliance)
- [Performance & Monitoring](#performance--monitoring)
- [Contributing](#contributing)
- [Support](#support)

## 🎯 Overview

The Healthcare Voice AI Assistant is a sophisticated, production-ready system that combines cutting-edge AI technologies to deliver intelligent healthcare information retrieval through natural voice interaction. Built with enterprise-grade architecture, it provides secure, scalable, and compliant healthcare knowledge management.

### Key Capabilities

- **Intelligent Voice Processing**: High-accuracy speech-to-text with OpenAI Whisper
- **Advanced RAG Pipeline**: Context-aware information retrieval with FAISS vector storage
- **Natural Language Understanding**: GPT-4 powered conversation intelligence
- **Professional Voice Synthesis**: High-quality text-to-speech via ElevenLabs
- **Enterprise Security**: Comprehensive security measures and compliance features
- **Scalable Architecture**: Microservices-based design with async processing

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │    │   API Gateway   │    │   Core Services │
│   (Web/React)   │◄──►│   (FastAPI)     │◄──►│   (RAG/LLM)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Middleware    │    │   Data Layer    │
                       │ (Security/Log)  │    │ (Vector/Storage)│
                       └─────────────────┘    └─────────────────┘
```

### Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Backend Framework** | FastAPI | ≥0.104.0 | High-performance API server |
| **Speech Recognition** | OpenAI Whisper | Latest | High-accuracy STT |
| **Vector Database** | FAISS | ≥1.7.4 | Efficient similarity search |
| **Language Model** | OpenAI GPT-4 | Latest | Intelligent conversation |
| **Text-to-Speech** | ElevenLabs | Latest | Natural voice synthesis |
| **Vector Embeddings** | OpenAI text-embedding-3-large | Latest | Semantic understanding |
| **Audio Processing** | PyAudio + Librosa | Latest | Real-time audio handling |

### Data Flow Architecture

1. **Voice Input** → Audio capture and preprocessing
2. **Speech Recognition** → Whisper API transcription
3. **Query Processing** → Intent extraction and context analysis
4. **Vector Search** → FAISS similarity search with embeddings
5. **Context Assembly** → Relevant document retrieval and ranking
6. **Response Generation** → GPT-4 powered answer synthesis
7. **Voice Output** → ElevenLabs TTS with natural intonation

## ✨ Features

### Core Functionality
- **Real-time Voice Interaction**: Seamless voice input/output with <2s latency
- **Intelligent Context Management**: Advanced conversation memory with configurable TTL
- **Multi-modal Input Support**: Voice, text, and file upload capabilities
- **Dynamic Response Generation**: Context-aware, personalized healthcare information

### Advanced Capabilities
- **Semantic Search**: Deep understanding of medical terminology and concepts
- **Hallucination Prevention**: Built-in safeguards against AI-generated misinformation
- **Multi-language Support**: Extensible framework for international deployments
- **Offline Capabilities**: Local processing options for sensitive environments

### Enterprise Features
- **Comprehensive Logging**: Structured logging with configurable levels and formats
- **Performance Monitoring**: Built-in metrics, health checks, and alerting
- **Rate Limiting**: Configurable request throttling and abuse prevention
- **Security Middleware**: CORS, trusted hosts, and input validation

## 🚀 Installation

### System Requirements

| Requirement | Specification | Notes |
|-------------|---------------|-------|
| **Python** | 3.9+ | CPython recommended |
| **Memory** | 4GB+ RAM | 8GB+ for production |
| **Storage** | 10GB+ free space | For models and data |
| **Audio** | Microphone + Speakers | USB or built-in |
| **Network** | Stable internet | For API services |

### Prerequisites

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y python3.9 python3.9-venv python3.9-dev
sudo apt-get install -y ffmpeg portaudio19-dev

# Install system dependencies (macOS)
brew install python@3.9 ffmpeg portaudio

# Install system dependencies (Windows)
# Download and install Python 3.9+ from python.org
# Install FFmpeg from https://ffmpeg.org/download.html
```

### Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/your-org/voice-RAG-assistant.git
cd voice-RAG-assistant

# 2. Create virtual environment
python3.9 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Setup environment configuration
python setup_env.py

# 5. Verify installation
python -c "import fastapi, openai, faiss; print('Installation successful')"
```

### Post-Installation Verification

```bash
# Test core components
python -m pytest tests/ -v --tb=short

# Verify API endpoints
python test_api.py

# Check system health
curl http://localhost:8000/health
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following configuration:

```bash
# =============================================================================
# CORE APPLICATION SETTINGS
# =============================================================================
ENVIRONMENT=development                    # development|staging|production
DEBUG=true                                # Enable debug mode
HOST=0.0.0.0                             # Bind address
PORT=8000                                 # Service port
LOG_LEVEL=INFO                            # Logging verbosity
SECRET_KEY=your-super-secret-key-here     # Application secret (32+ chars)

# =============================================================================
# OPENAI CONFIGURATION
# =============================================================================
OPENAI_API_KEY=sk-...                     # OpenAI API key (required)
OPENAI_MODEL=gpt-4                        # LLM model identifier
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_MAX_TOKENS=1000                    # Maximum response length
OPENAI_TEMPERATURE=0.1                    # Response creativity (0.0-1.0)

# =============================================================================
# ELEVENLABS TTS CONFIGURATION
# =============================================================================
ELEVENLABS_API_KEY=...                    # ElevenLabs API key (required)
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM # Voice identifier
ELEVENLABS_MODEL_ID=eleven_monolingual_v1 # TTS model

# =============================================================================
# RAG PIPELINE CONFIGURATION
# =============================================================================
EMBEDDING_MODEL=text-embedding-3-large    # Vector embedding model
TOP_K_RESULTS=5                           # Number of search results
CHUNK_SIZE=1000                           # Document chunk size
CHUNK_OVERLAP=200                         # Chunk overlap size
SIMILARITY_THRESHOLD=0.7                  # Minimum similarity score

# =============================================================================
# VOICE PROCESSING CONFIGURATION
# =============================================================================
SAMPLE_RATE=16000                          # Audio sample rate (Hz)
CHUNK_DURATION_MS=1000                     # Audio chunk duration
MAX_RECORDING_TIME=30                      # Maximum recording length (s)
VAD_MODE=3                                 # Voice activity detection mode

# =============================================================================
# SECURITY & COMPLIANCE
# =============================================================================
ENABLE_RATE_LIMITING=true                  # Enable request throttling
MAX_REQUESTS_PER_MINUTE=60                # Rate limit per minute
CORS_ORIGINS=["http://localhost:3000"]     # Allowed origins
HEALTHCARE_DISCLAIMER=true                 # Enable medical disclaimers
BLOCK_MEDICAL_ADVICE=true                  # Block unsafe medical content
```

### Configuration Validation

```bash
# Validate configuration
python -c "
from config.settings import get_settings
settings = get_settings()
print(f'Configuration loaded: {settings.environment}')
print(f'OpenAI configured: {bool(settings.openai_api_key)}')
print(f'ElevenLabs configured: {bool(settings.elevenlabs_api_key)}')
"
```

## 🔌 API Reference

### Base URL
```
Development: http://localhost:8000
Production: https://your-domain.com
```

### Authentication
All API endpoints require proper authentication headers:

```bash
# For protected endpoints
Authorization: Bearer <your-api-token>
Content-Type: application/json
```

### Core Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "openai": "connected",
    "elevenlabs": "connected",
    "vector_store": "ready"
  }
}
```

#### Voice Transcription
```http
POST /api/voice/transcribe
Content-Type: multipart/form-data

Body: audio file (wav, mp3, m4a, flac)
```

**Response:**
```json
{
  "transcript": "What are the symptoms of diabetes?",
  "confidence": 0.95,
  "language": "en",
  "processing_time_ms": 1200
}
```

#### Chat Completion
```http
POST /api/chat
Content-Type: application/json

{
  "message": "What are the symptoms of diabetes?",
  "conversation_id": "conv_123",
  "include_sources": true
}
```

**Response:**
```json
{
  "response": "Diabetes symptoms include increased thirst, frequent urination...",
  "sources": [
    {
      "title": "Diabetes Management Guide",
      "confidence": 0.89,
      "excerpt": "Common symptoms of diabetes..."
    }
  ],
  "conversation_id": "conv_123",
  "processing_time_ms": 1800
}
```

#### Voice Synthesis
```http
POST /api/voice/synthesize
Content-Type: application/json

{
  "text": "Here is your response...",
  "voice_id": "21m00Tcm4TlvDq8ikWAM"
}
```

**Response:**
```json
{
  "audio_url": "/api/voice/audio/generated_123.wav",
  "duration_ms": 3500,
  "word_count": 25
}
```

### Error Handling

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "message",
      "issue": "Field is required"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123"
}
```

## 📖 Usage Guide

### Web Interface

1. **Access the Application**
   - Navigate to `http://localhost:8000`
   - Ensure microphone permissions are granted

2. **Voice Interaction**
   - Click the microphone button to start recording
   - Speak your healthcare question clearly
   - Release the button to process your query
   - Listen to the AI-generated response

3. **Text Interface**
   - Type your question in the text input field
   - Press Enter or click Send
   - View the response with source citations

### Voice Commands

| Command | Action | Example |
|---------|--------|---------|
| **"Stop"** | Interrupt current response | "Stop, that's enough" |
| **"Repeat"** | Replay last response | "Can you repeat that?" |
| **"Clear"** | Reset conversation memory | "Clear our conversation" |
| **"Help"** | Show available commands | "What can I ask you?" |
| **"Sources"** | Request source information | "What are your sources?" |

### Best Practices

- **Clear Speech**: Speak at normal pace with clear pronunciation
- **Specific Questions**: Ask specific questions for better responses
- **Context Maintenance**: Reference previous conversation for continuity
- **Source Verification**: Always verify information from authoritative sources

## 🛠️ Development

### Development Environment Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Setup pre-commit hooks
pre-commit install

# Configure development tools
cp .env.example .env
# Edit .env with your development API keys
```

### Code Quality Standards

```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy .

# Run tests
pytest tests/ -v --cov=. --cov-report=html
```

### Project Structure

```
voice-RAG-assistant/
├── app/                           # FastAPI application
│   ├── api/                      # API endpoint definitions
│   │   ├── chat.py              # Chat completion endpoints
│   │   ├── voice.py             # Voice processing endpoints
│   │   ├── health.py            # Health monitoring
│   │   └── docs.py              # API documentation
│   └── middleware.py             # Custom middleware
├── config/                        # Configuration management
│   └── settings.py               # Environment-based settings
├── rag/                          # RAG pipeline components
│   ├── document_processor.py     # Document ingestion and processing
│   ├── embedding_client.py       # Vector embedding generation
│   └── rag_pipeline.py          # Core RAG orchestration
├── llm/                          # Language model integration
│   └── openai_client.py         # OpenAI API client
├── stt/                          # Speech-to-text services
│   └── whisper_client.py        # OpenAI Whisper integration
├── tts/                          # Text-to-speech services
│   └── elevenlabs_client.py     # ElevenLabs TTS client
├── safety/                       # Content safety and compliance
│   └── healthcare_filter.py     # Healthcare content filtering
├── memory/                       # Conversation management
│   └── conversation_memory.py   # Memory and context handling
├── utils/                        # Utility functions
│   └── logger.py                # Logging configuration
├── frontend/                     # Web interface
│   └── static/                  # Static assets (HTML, CSS, JS)
├── scripts/                      # Utility scripts
│   └── ingest.py                # Document ingestion pipeline
├── tests/                        # Test suite
├── data/                         # Data storage
│   └── vector_store/            # FAISS index storage
├── uploads/                      # Temporary file storage
├── logs/                         # Application logs
├── main.py                       # Application entry point
├── setup_env.py                  # Environment configuration helper
├── requirements.txt              # Python dependencies
└── README.md                     # This documentation
```

### Testing Strategy

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# End-to-end tests
pytest tests/e2e/ -v

# Performance tests
pytest tests/performance/ -v

# Coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing
```

## 🚀 Deployment

### Production Deployment

#### Docker Deployment
```bash
# Build production image
docker build -t healthcare-voice-ai:latest .

# Run with environment variables
docker run -d \
  --name healthcare-voice-ai \
  -p 8000:8000 \
  --env-file .env.production \
  --restart unless-stopped \
  healthcare-voice-ai:latest
```

#### Docker Compose
```yaml
version: '3.8'
services:
  healthcare-voice-ai:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: healthcare-voice-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: healthcare-voice-ai
  template:
    metadata:
      labels:
        app: healthcare-voice-ai
    spec:
      containers:
      - name: healthcare-voice-ai
        image: healthcare-voice-ai:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

### Environment-Specific Configurations

#### Development
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_DEBUG_ENDPOINTS=true
```

#### Staging
```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
ENABLE_DEBUG_ENDPOINTS=false
```

#### Production
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
ENABLE_DEBUG_ENDPOINTS=false
ENABLE_RATE_LIMITING=true
```

## 🔒 Security & Compliance

### Security Features

- **API Key Management**: Secure storage and rotation of API keys
- **Rate Limiting**: Configurable request throttling to prevent abuse
- **Input Validation**: Comprehensive validation of all user inputs
- **CORS Protection**: Configurable cross-origin resource sharing
- **Trusted Hosts**: Host validation for production deployments
- **Secret Management**: Secure handling of application secrets

### Healthcare Compliance

- **HIPAA Awareness**: Built-in safeguards for healthcare data handling
- **Content Filtering**: Automatic detection and blocking of unsafe medical advice
- **Disclaimer System**: Mandatory medical disclaimers on all responses
- **Audit Logging**: Comprehensive logging of all system interactions
- **Data Privacy**: Secure handling and storage of user data

### Security Best Practices

```bash
# Generate secure secret key
openssl rand -hex 32

# Regular security updates
pip install --upgrade -r requirements.txt

# Security scanning
bandit -r .
safety check

# Dependency vulnerability scanning
pip-audit
```

## 📊 Performance & Monitoring

### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Response Time** | <2s | End-to-end latency |
| **Transcription Accuracy** | >95% | Whisper API accuracy |
| **Throughput** | 100+ req/min | Concurrent request handling |
| **Uptime** | 99.9% | System availability |
| **Memory Usage** | <1GB | Application memory footprint |

### Monitoring & Alerting

#### Health Checks
```bash
# Application health
curl http://localhost:8000/health

# Detailed health status
curl http://localhost:8000/health/detailed

# Metrics endpoint
curl http://localhost:8000/metrics
```

#### Logging Configuration
```python
# Structured logging with JSON format
import loguru

logger = loguru.logger
logger.add(
    "logs/app.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO",
    rotation="1 day",
    retention="30 days"
)
```

#### Performance Monitoring
```bash
# Monitor system resources
htop
iotop
nethogs

# Application profiling
python -m cProfile -o profile.stats main.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

## 🤝 Contributing

We welcome contributions from the community! Please follow our contribution guidelines:

### Contribution Process

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/voice-RAG-assistant.git
   cd voice-RAG-assistant
   git remote add upstream https://github.com/original-org/voice-RAG-assistant.git
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make Changes**
   - Follow the coding standards
   - Add comprehensive tests
   - Update documentation
   - Ensure all tests pass

4. **Submit Pull Request**
   - Provide clear description of changes
   - Include test results
   - Reference related issues

### Development Standards

- **Code Style**: Follow PEP 8 and Black formatting
- **Type Hints**: Use type hints for all function parameters and returns
- **Documentation**: Include docstrings for all public functions
- **Testing**: Maintain >90% code coverage
- **Security**: Follow security best practices

### Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Security considerations addressed
- [ ] Performance impact assessed
- [ ] Error handling implemented

## 🆘 Support

### Getting Help

1. **Documentation**: Review this README and inline code documentation
2. **Issues**: Check existing issues in the GitHub repository
3. **Discussions**: Use GitHub Discussions for questions and ideas
4. **Security**: Report security issues privately to security@your-org.com

### Troubleshooting

#### Common Issues

**Audio Recording Problems**
```bash
# Check audio permissions
ls -la /dev/snd/
# Verify PyAudio installation
python -c "import pyaudio; print('PyAudio working')"
```

**API Connection Issues**
```bash
# Test OpenAI connection
python -c "import openai; print(openai.Model.list())"
# Test ElevenLabs connection
curl -H "xi-api-key: YOUR_KEY" https://api.elevenlabs.io/v1/voices
```

**Performance Issues**
```bash
# Monitor system resources
top -p $(pgrep -f "python.*main.py")
# Check log files
tail -f logs/app.log
```

### Community Resources

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Community support and Q&A
- **Wiki**: Additional documentation and guides
- **Examples**: Sample implementations and use cases

## 🔮 Roadmap

### Short-term Goals (Q1 2024)
- [ ] Enhanced multi-language support
- [ ] Advanced conversation memory with vector search
- [ ] Real-time collaboration features
- [ ] Mobile-responsive UI improvements

### Medium-term Goals (Q2-Q3 2024)
- [ ] Mobile application development
- [ ] Integration with EHR systems
- [ ] Advanced analytics and insights dashboard
- [ ] Custom voice model training capabilities

### Long-term Vision (Q4 2024+)
- [ ] Offline mode support
- [ ] Edge computing deployment
- [ ] Advanced AI model fine-tuning
- [ ] Enterprise SSO integration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Important Disclaimers

### Medical Disclaimer
**This system is for educational and development purposes only.** It is not intended for clinical use and should not replace professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare professionals for medical decisions.

### AI Limitations
While this system uses advanced AI models, responses may contain inaccuracies or hallucinations. Users should verify all information independently and never rely solely on AI-generated medical information.

### Privacy & Compliance
This system processes voice and text data. Ensure compliance with local privacy regulations (HIPAA, GDPR, etc.) and implement appropriate data handling practices for production use.

### Security Considerations
- Regularly update dependencies and security patches
- Implement proper access controls and authentication
- Monitor system logs for suspicious activity
- Follow security best practices for healthcare applications

---

**Built with  for the healthcare community**

*For questions, support, or contributions, please visit our [GitHub repository](https://github.com/your-org/voice-RAG-assistant).*


