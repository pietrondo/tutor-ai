# 🎓 Tutor AI - Quick Start & Setup

<div align="center">

![Tutor AI Logo](https://img.shields.io/badge/Tutor-AI-Blue?style=for-the-badge&logo=openai&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-16.0.1-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green?logo=fastapi)](https://fastapi.tiangolo.com/)

**An intelligent tutoring system for university courses with AI-powered learning**

</div>

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker & Docker Compose (recommended)

### Option 1: Docker (Recommended)
```bash
# Clone and start
git clone <repository-url>
cd tutor-ai
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Access
# Frontend: http://localhost:3000
# Backend: http://localhost:8001
```

### Option 2: Local Development
```bash
# Backend
cd backend && pip install -r requirements.txt && python3 main.py &

# Frontend
cd ../frontend && npm install && npm run dev
```

### Environment Setup
Copy `.env.example` to `.env` and configure API keys:
```env
OPENAI_API_KEY=your_key
OPENROUTER_API_KEY=your_key
ZAI_API_KEY=your_key
LOCAL_LLM_URL=http://localhost:11434/v1
```

## ✨ Key Features

- **🤖 Multi-Provider AI**: OpenAI, OpenRouter, Z.AI, local models
- **📚 Document Processing**: PDF upload, OCR, vector indexing
- **💬 AI Chat**: RAG-powered conversations with source attribution
- **📊 Analytics**: Progress tracking and learning insights
- **🧠 Cognitive Learning**: Spaced Repetition, Active Recall, Dual Coding
- **🎨 Visualizations**: Concept maps and interactive charts
- **📝 Assessment**: Auto-generated quizzes with multiple formats

## 🏗️ Architecture

### Backend (FastAPI)
- Python 3.9+, FastAPI 0.115.0
- AI: LangChain, ChromaDB, Sentence Transformers
- Database: SQLAlchemy with SQLite
- Document: PyMuPDF, Tesseract, OpenCV

### Frontend (Next.js)
- Next.js 16.0.1, React 19.2.0, TypeScript
- Styling: TailwindCSS 4.1.16
- State: Zustand, React Query
- UI: Headless UI, Radix primitives

## 📁 Project Structure

```
tutor-ai/
├── backend/           # FastAPI backend
│   ├── services/      # Core business logic
│   ├── models/        # Data models
│   └── main.py       # Entry point
├── frontend/          # Next.js frontend
│   ├── src/app/      # App Router pages
│   ├── components/   # React components
│   └── lib/          # Utilities
├── data/             # Local storage
└── docker-compose.yml
```

## 🛠️ Common Commands

### Docker
```bash
# Start development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Local Development
```bash
# Backend
cd backend && python3 main.py

# Frontend
cd frontend && npm run dev

# Tests
cd backend && python -m pytest test_*.py
cd frontend && npm run test
```

## 🔧 Important Ports

- **Frontend**: 3000
- **Backend**: 8001
- **CORS**: `http://localhost:3000,http://127.0.0.1:3000`

## 📚 Key API Endpoints

### Courses
- `GET /courses` - List courses
- `POST /courses` - Create course
- `GET /courses/{id}` - Get course details

### AI Chat
- `POST /chat` - General AI chat
- `POST /course-chat` - Course-specific chat
- `POST /search` - Document search

### Cognitive Learning
- `POST /api/spaced-repetition/card` - Create flashcard
- `POST /api/active-recall/generate-questions` - Generate questions
- `POST /api/dual-coding/create` - Visual learning content

## 🆘 Troubleshooting

### Common Issues
1. **Port conflicts**: Ensure ports 3000 and 8001 are available
2. **API keys**: Check `.env` file configuration
3. **Docker permissions**: `sudo chown -R $USER:$USER data/`
4. **Memory issues**: Increase container memory limits

### Reset System
```bash
docker-compose down --volumes --remove-orphans
docker system prune -f
rm -rf frontend/.next data/vector_db/*
docker-compose up --build
```

## 📖 Additional Documentation

- `CLAUDE_DETAILED.md` - Complete system documentation
- `CLAUDE_API.md` - API reference
- `CLAUDE_CLE.md` - Cognitive Learning Engine
- `LOCAL_SETUP.md` - Development setup guide

---

<div align="center">

**🚀 Version: 2.0.0** • **📅 Updated: 2025-11-08** • **⭐ MIT License**

</div>