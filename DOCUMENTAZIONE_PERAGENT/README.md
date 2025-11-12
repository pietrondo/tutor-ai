# 📚 Tutor-AI Technical Documentation

**Piattaforma di tutoraggio intelligente basata su AI avanzata con cognitive science**

---

## 🎯 Panoramica del Sistema

Tutor-AI è una piattaforma educativa avanzata che integra modelli linguistici di ultima generazione (GLM-4.6, Claude-3.5) con principi di scienze cognitive per fornire esperienze di apprendimento personalizzate ed efficaci.

### 🏗️ Architettura Principale
- **Backend**: FastAPI 0.115.0 con 40+ servizi specializzati
- **Frontend**: Next.js 16.0.1 con routing dinamico e componenti React/TypeScript
- **AI Integration**: Multi-provider LLM con RAG system e optimization continua
- **Database**: SQLAlchemy + ChromaDB + File system storage
- **Containerization**: Docker Compose con multi-environment support

### 🚀 Funzionalità Principali
- **Gestione Corsi**: Upload, organizzazione, e accesso a materiali didattici
- **Chat Intelligente**: Session-based tutoring con RAG e context awareness
- **Learning Analytics**: Tracking avanzato e metacognitive monitoring
- **PDF Integration**: Lettori multi-tecnologia con sistema annotazioni
- **Cognitive Learning Engine**: 5 fasi implementate con evidence-based principles

---

## 📋 Indice della Documentazione

### **Backend (`backend/`)**
- **[Overview](backend/overview.md)** - Architettura FastAPI, servizi, e integrazioni
- **[Endpoints](backend/endpoints.md)** - Catalogo completo di tutte le API REST
- **[Services](backend/services.md)** - Dettaglio di tutti i servizi implementati
- **[Database](backend/database.md)** - Schema SQLAlchemy, modelli, e strutture dati
- **[Logging](backend/logging.md)** - Sistema di logging strutturato e monitoring

### **Frontend (`frontend/`)**
- **[Overview](frontend/overview.md)** - Architettura Next.js, routing dinamico, componenti
- **[Components](frontend/components.md)** - Catalogo completo componenti React/TypeScript
- **[Routing](frontend/routing.md)** - Struttura routing dinamico e gestione parametri
- **[Chat & Study](frontend/chat-study.md)** - Sistema chat tutoring e workspace studio

### **Intelligenza Artificiale (`ai/`)**
- **[Models](ai/models.md)** - Modelli LLM supportati e configurazione
- **[RAG & LLM](ai/rag-llm.md)** - Sistema RAG, orchestrazione, e best practices
- **[Cognitive Learning Engine](ai/cognitive-learning.md)** - Motore di apprendimento basato su scienze cognitive

### **Infrastruttura (`infrastructure/`)**
- **[Setup](infrastructure/setup.md)** - Guida installazione e configurazione locale
- **[Docker](infrastructure/docker.md)** - Containerizzazione e orchestrazione
- **[Environment Variables](infrastructure/env-vars.md)** - Variabili d'ambiente complete
- **[Deployment](infrastructure/deployment.md)** - Produzione, monitoring, e manutenzione

### **API Reference (`api/`)**
- **[Complete Reference](api/complete-reference.md)** - Referenza completa di tutte le API
- **[Examples](api/examples.md)** - Esempi pratici di utilizzo delle API

---

## 🔍 Accesso Rapido per Componenti

### Backend Services Key
- **RAG Service**: Retrieval-Augmented Generation con ChromaDB
- **LLM Service**: Multi-provider (OpenAI, ZAI, OpenRouter, Local)
- **Course Service**: Gestione corsi, libri, e materiali didattici
- **CLE Services**: Spaced Repetition, Active Recall, Dual Coding
- **Annotation Service**: Sistema annotazioni PDF con sincronizzazione

### API Endpoints Principal
- **Course Management**: `/api/courses/*` (CRUD corsi e materiali)
- **Chat & Tutoring**: `/api/chat/*`, `/api/course-chat/*` (sessioni chat)
- **Cognitive Learning**: `/api/spaced-repetition/*`, `/api/active-recall/*`
- **PDF Operations**: `/api/materials/*` (upload, processing, accesso)
- **Analytics**: `/api/progress/*` (tracking e learning analytics)

### Frontend Components Key
- **Course Management**: `CourseCard`, `BookCard`, navigation
- **Chat Interface**: `ChatInterface`, `ChatMessage`, `IntegratedChatTutor`
- **PDF Readers**: `EnhancedPDFReader`, annotazioni e workspace
- **Learning Components**: `StudyProgress`, `ConceptVisualization`
- **UI Components**: Libreria condivisa con TypeScript

---

## 🛠️ Quick Start Guide

### 1. Setup Ambiente di Sviluppo
```bash
# Clone repository
git clone <repository-url>
cd tutor-ai

# Avvio con script unificato
./start.sh dev

# Accesso applicazione
# Frontend: http://localhost:3001
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 2. Configurazione Chiave
```env
# Backend (.env)
OPENAI_API_KEY=your_key
ZAI_API_KEY=your_key
LOCAL_LLM_URL=http://localhost:11434/v1

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Struttura Progetto
```
tutor-ai/
├── backend/                    # FastAPI backend
│   ├── services/               # 40+ servizi specializzati
│   ├── models/                # SQLAlchemy models
│   ├── app/api/               # API endpoints
│   └── main.py               # Application entry point
├── frontend/                  # Next.js frontend
│   ├── src/app/              # App Router pages
│   ├── src/components/         # React components
│   └── src/lib/               # Utilities
├── DOCUMENTAZIONE_PERAGENT/     # Questa documentazione
└── data/                      # Storage dati
    ├── courses/              # Course materials
    ├── vector_db/            # ChromaDB storage
    └── uploads/               # File uploads
```

---

## 🔧 Configurazione Avanzata

### Port Standardizzazione
- **Backend**: Port 8000 (NON 8001)
- **Frontend**: Port 3001 (NON 3000 o 4000)
- **Redis**: Port 6379
- **CORS Origins**: `http://localhost:3001,http://127.0.0.1:3001`

### Environment Variables Complete
```bash
# Core Configuration
LLM_TYPE=openai
OPENAI_API_KEY=sk-*
ZAI_API_KEY=your_zai_key
LOCAL_LLM_URL=http://localhost:11434/v1

# Database
DATABASE_URL=sqlite:///./data/app.db
VECTOR_DB_PATH=./data/vector_db
REDIS_URL=redis://localhost:6379

# Performance
UPLOAD_DIR=./data/uploads
CORS_ORIGINS=http://localhost:3001,http://127.0.0.1:3001
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs
ENABLE_PERFORMANCE_LOGGING=true
```

---

## 🚀 Features Avanzate

### Motore di Apprendimento Cognitivo (CLE)
1. **Spaced Repetition System** - Enhanced SM-2 con auto-generazione
2. **Active Recall Engine** - Multi-format questions across Bloom's taxonomy
3. **Dual Coding Service** - Visual-verbal integration con 10 element types
4. **Interleaved Practice** - Session manager per interleaving
5. **Metacognition Framework** - Self-regulation e monitoring

### AI Integration Avanzata
- **ModelSelector 2.0**: Routing intelligente GLM-4.6/Claude-3.5
- **Multi-Provider Support**: OpenAI, Z.AI, OpenRouter, Local models
- **Continuous Improvement**: ML-based prompt optimization
- **A/B Testing Framework**: Statistical testing con multiple strategies
- **Performance Analytics**: Real-time monitoring e optimization

### PDF Integration
- **Multi-Tecnologia**: ReactPDF, pdf.js, PyMuPDF
- **Sistema Annotazioni**: Highlight, underline, notes, condivisibili con AI
- **Workspace Studio**: Ambiente integrato studio + chat
- **Dynamic Routing**: Accesso diretto ai materiali con parametri URL
- **Local Storage**: Tutti i PDF mantenuti localmente per affidabilità

---

## 📊 Performance e Scalability

### Metriche di Sistema
- **Response Time**: <2s per richiesta media
- **Availability**: 99.9% uptime target
- **Concurrent Users**: 1000+ utenti simultanei
- **Database Performance**: Query optimization con indici
- **AI Model Performance**: <1s generazione risposta media

### Monitoring e Analytics
- **Structured Logging**: JSON format con correlation IDs
- **Performance Monitoring**: Tempo risposta e success rate
- **Learning Analytics**: Tracking progress e metacognition
- **Error Tracking**: Categorizzazione automatica errori
- **Health Checks**: Container e service health monitoring

---

## 🔍 Troubleshooting Guida

### Issues Comuni e Soluzioni
- **Port Conflicts**: Verifica configurazione porte 8000/3001
- **Dynamic Routes 404**: Usa `./start.sh dev` NON produzione
- **PDF Loading Errors**: Controlla file permissions e paths
- **AI Provider Issues**: Verifica API keys e connettività
- **Database Connection**: Controlla permessi directory `./data`

### Debug Commands
```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:3001

# Container status
docker-compose ps
docker-compose logs backend
docker-compose logs frontend

# Port conflicts
ss -tulpn | grep :8000
ss -tulpn | grep :3001
```

---

## 📈 Futuro e Estensioni

### Roadmap Prossima
- **Voice AI Integration**: Modelli vocali per interazioni naturali
- **Advanced Analytics**: ML insights per personalizzazione
- **Multi-language Support**: Supporto internazionale
- **Enterprise Features**: SSO, RBAC, compliance
- **Mobile Apps**: Native iOS/Android applications

### Estensioni Tecniche
- **GraphQL API**: Query optimization
- **Microservices**: Service decomposition
- **Event Streaming**: Real-time notifications
- **Cache Layers**: Redis optimization
- **CDN Integration**: Global content delivery

---

## 📞 Support e Contatti

### Support Tecnico
- **Issues**: Repository Issues per bug reports
- **Documentazione**: Questa wiki per riferimenti tecnici
- **Community**: Forum/discussion per best practices

### Development Team
- **Architecture**: Design patterns e decisioni tecniche
- **API Reference**: Documentazione endpoints aggiornata
- **Testing**: Suite completa con Docker integration

---

*Ultimo aggiornamento: Novembre 2025*
*Versione: 2.0.0*
*Licenza: MIT*