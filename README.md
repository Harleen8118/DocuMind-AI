# DocuMind AI

> **Upload PDFs, audio, and video - then chat with AI about your content.**

DocuMind AI is a full-stack web application that lets users upload documents, audio recordings, and video files, then have intelligent conversations with an AI that understands the content. It includes transcription, semantic search, timestamps, and a media player that jumps to relevant moments.

## ✨ Standout Feature: Smart Highlight Reel

After a video is processed, DocuMind automatically generates a list of the **top 5 most important moments** with timestamps and one-line summaries, displayed as clickable cards that jump the video player to that exact moment.

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   React + Vite  │────▶│  FastAPI Backend │
│   TailwindCSS   │     │   Python 3.11   │
│   shadcn/ui     │     └────────┬────────┘
└─────────────────┘              │
                          ┌──────┴──────┐
                    ┌─────┤  Services   ├─────┐
                    │     └─────────────┘     │
              ┌─────┴─────┐           ┌──────┴──────┐
              │  Gemini   │           │   Whisper   │
              │  1.5 Flash│           │  (Local)    │
              └───────────┘           └─────────────┘
                    │                       │
              ┌─────┴─────┐           ┌─────┴─────┐
              │   FAISS   │           │  ffmpeg    │
              │  Vectors  │           │  Audio Ext │
              └───────────┘           └───────────┘
                    │
         ┌─────────┴──────────┐
         │                    │
   ┌─────┴─────┐      ┌──────┴──────┐
   │ PostgreSQL │      │    Redis    │
   │  Metadata  │      │   Cache    │
   └───────────┘      └────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/documind-ai.git
   cd documind-ai
   ```

2. **Configure environment**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your GEMINI_API_KEY
   ```

3. **Start all services**
   ```bash
   docker compose up --build
   ```

4. **Open the app**
   - Frontend: [http://localhost:5173](http://localhost:5173)
   - API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📁 Project Structure

```
documind/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # App entry, CORS, routers
│   │   ├── config.py       # Settings via pydantic-settings
│   │   ├── database.py     # Async SQLAlchemy
│   │   ├── models/         # ORM models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── middleware/      # Rate limiting
│   │   └── utils/          # Helpers
│   └── tests/              # pytest suite
├── frontend/               # React + Vite frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── store/          # Zustand state
│   │   └── api/            # Axios client
│   └── tests/              # Vitest suite
├── docker-compose.yml
└── .github/workflows/      # CI/CD
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Get JWT token |
| GET | `/api/v1/auth/me` | Current user info |
| POST | `/api/v1/documents/upload` | Upload file |
| GET | `/api/v1/documents/` | List documents |
| DELETE | `/api/v1/documents/{id}` | Delete document |
| POST | `/api/v1/documents/{id}/summarize` | Generate summary |
| GET | `/api/v1/documents/{id}/highlights` | Get highlight reel |
| POST | `/api/v1/chat/sessions` | Create chat session |
| GET | `/api/v1/chat/sessions` | List sessions |
| POST | `/api/v1/chat/sessions/{id}/messages` | Send message (SSE) |
| GET | `/api/v1/chat/sessions/{id}/messages` | Get message history |

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest --cov=app --cov-report=term-missing -v

# Frontend tests
cd frontend
npx vitest run
```

## 🛠️ Tech Stack

**Backend:** Python 3.11, FastAPI, Google Gemini 2.5 Flash, Whisper, PyMuPDF, FAISS, sentence-transformers, PostgreSQL, Redis, JWT

**Frontend:** React 18, Vite, TailwindCSS, shadcn/ui, TanStack Query, Wavesurfer.js, React-PDF, Zustand

**Infrastructure:** Docker, Docker Compose, GitHub Actions