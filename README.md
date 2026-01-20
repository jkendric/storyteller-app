# Storyteller - Dynamic Story Generation Platform

A web-based episodic story generation platform that generates short-form fiction episode-by-episode, streams text in real-time, provides audiobook-style TTS narration, and supports story forking.

## Features

- **Episodic Story Generation**: Generate stories episode by episode with AI
- **Real-time Streaming**: Watch text appear token-by-token as it's generated
- **Text-to-Speech**: Audiobook-style narration with Kokoro TTS
- **Story Forking**: Branch your stories at any episode to explore alternate paths
- **Character Management**: Create and manage reusable characters
- **Scenario Templates**: Define settings, genres, and world rules
- **3-Tier Memory System**: Maintains story continuity across episodes
- **Dark Theme UI**: Beautiful, responsive dark-themed interface

## Technology Stack

| Component | Technology |
|-----------|------------|
| Frontend | React 18 + Vite + TypeScript + TailwindCSS |
| Backend | Python FastAPI + SQLite |
| LLM | Ollama (configurable model) |
| TTS | Kokoro-FastAPI (OpenAI-compatible) |
| State Management | Zustand |
| Deployment | Docker Compose |

## Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend)
- **Ollama** (for LLM generation)
- **Kokoro-FastAPI** (optional, for TTS)
- **NVIDIA GPU** (recommended for performance)

## Quick Start

### 1. Clone and Setup

```bash
cd D:\_DEV\storyteller-app

# Copy environment file
cp .env.example .env
```

### 2. Install Ollama and Pull a Model

```bash
# Install Ollama from https://ollama.ai
# Then pull a model:
ollama pull llama3.2

# Or for better quality:
ollama pull mistral
```

### 3. Start Kokoro TTS (Optional)

```bash
# GPU version (recommended)
docker run -d --gpus all -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-gpu:latest

# CPU version
docker run -d -p 8880:8880 ghcr.io/remsky/kokoro-fastapi:latest
```

### 4. Start the Backend

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### 6. Open the Application

Navigate to http://localhost:5173 in your browser.

## Docker Deployment

For production deployment using Docker Compose:

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The application will be available at http://localhost (port 80).

## Configuration

### Environment Variables

Edit `.env` to configure the application:

```env
# Database
DATABASE_URL=sqlite:///./data/storyteller.db

# Ollama LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Kokoro TTS
KOKORO_TTS_URL=http://localhost:8880
TTS_DEFAULT_VOICE=af_bella

# Story Generation
EPISODE_TARGET_WORDS=1250
```

### Available TTS Voices

| Voice ID | Name | Language |
|----------|------|----------|
| af_bella | Bella | American English (Female) |
| af_sarah | Sarah | American English (Female) |
| am_adam | Adam | American English (Male) |
| am_michael | Michael | American English (Male) |
| bf_emma | Emma | British English (Female) |
| bm_george | George | British English (Male) |

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# Run specific test file
python -m pytest tests/test_characters.py -v
```

### Frontend Tests

```bash
cd frontend

# Run tests once
npm run test:run

# Run tests in watch mode
npm run test

# Run with coverage
npm run test:run -- --coverage
```

### Test Coverage

**Backend Tests (21 tests):**
- Character CRUD operations (6 tests)
- Scenario CRUD operations (6 tests)
- Story CRUD operations (7 tests)
- Health check endpoints (2 tests)

**Frontend Tests (12 tests):**
- App rendering (2 tests)
- Story store state management (5 tests)
- Audio store state management (5 tests)

## Project Structure

```
storyteller-app/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings management
│   │   ├── database.py          # SQLite + SQLAlchemy
│   │   ├── models/              # ORM models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API endpoints
│   │   └── services/            # Business logic
│   ├── tests/                   # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                 # API client
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom hooks
│   │   ├── stores/              # Zustand stores
│   │   ├── pages/               # Route pages
│   │   └── test/                # Frontend tests
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env
└── README.md
```


## API Endpoints

### Characters
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/characters` | List all characters |
| POST | `/api/characters` | Create character |
| GET | `/api/characters/{id}` | Get character |
| PUT | `/api/characters/{id}` | Update character |
| DELETE | `/api/characters/{id}` | Delete character |

### Scenarios
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scenarios` | List all scenarios |
| POST | `/api/scenarios` | Create scenario |
| GET | `/api/scenarios/{id}` | Get scenario |
| PUT | `/api/scenarios/{id}` | Update scenario |
| DELETE | `/api/scenarios/{id}` | Delete scenario |

### Stories
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stories` | List all stories |
| POST | `/api/stories` | Create story |
| GET | `/api/stories/{id}` | Get story |
| PUT | `/api/stories/{id}` | Update story |
| DELETE | `/api/stories/{id}` | Delete story |
| POST | `/api/stories/{id}/fork` | Fork story |
| GET | `/api/stories/{id}/tree` | Get fork tree |

### Episodes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stories/{id}/episodes` | List episodes |
| POST | `/api/stories/{id}/episodes/generate` | Generate episode (SSE) |
| GET | `/api/stories/{id}/episodes/{num}` | Get episode |
| PUT | `/api/stories/{id}/episodes/{num}` | Update episode |
| DELETE | `/api/stories/{id}/episodes/{num}` | Delete episode |

### TTS
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tts/generate` | Generate audio |
| GET | `/api/tts/voices` | List voices |
| GET | `/api/tts/health` | TTS health check |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | System health check |
| GET | `/api/models` | List Ollama models |

## Usage Guide

### Creating a Story

1. **Create Characters**: Go to Characters page and define your protagonists, antagonists, and supporting characters with their personalities, motivations, and backstories.

2. **Create a Scenario**: Go to Scenarios page and set up the world - define the setting, time period, genre, tone, and any special rules for your story world.

3. **Start a Story**: Go to Stories → New Story, give it a title, select a scenario, and add characters with their roles.

4. **Generate Episodes**: In the story reader, click "Generate Episode" to create your first episode. Optionally provide narrative guidance to steer the story.

5. **Listen to Narration**: Toggle the audio player to hear your story read aloud with TTS.

6. **Fork the Story**: Click "Fork" to create an alternate timeline from any episode - explore different story directions!

### Memory System

The 3-tier memory system maintains story continuity:

- **Active Memory**: Full text of the last 3 episodes
- **Background Memory**: Summaries of episodes 4-10
- **Faded Memory**: Key facts from older episodes

This ensures the AI maintains consistent characters and plot even in long stories.

## Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

### TTS Not Working

```bash
# Check Kokoro health
curl http://localhost:8880/health

# Check available voices
curl http://localhost:8880/v1/audio/voices
```

### Database Issues

```bash
# Reset database (WARNING: deletes all data)
rm backend/data/storyteller.db
# Restart backend - database will be recreated
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests to ensure they pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
