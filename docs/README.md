# Tutor-AI Documentation

## 📚 **Documentazione Completa del Sistema**

Benvenuto nella documentazione completa del sistema Tutor-AI. Qui troverai tutte le informazioni necessarie per comprendere, configurare e manutenere la piattaforma.

## 🏗️ **Panoramica del Sistema**

Tutor-AI è una piattaforma di studio intelligente che utilizza l'AI per:
- Generazione automatica di presentazioni e slide
- Chat tutor personalizzato
- RAG (Retrieval Augmented Generation) per documenti
- Piani di studio personalizzati
- Quiz e valutazioni automatiche
- Tracciamento dei progressi

## 🚀 **Architettura**

```
Frontend (Next.js) ←→ Backend (FastAPI) ←→ LLM Services (ZAI/OpenAI/Ollama)
                                    ↓
                              Database & Storage
                                    ↓
                            PDF Generation & OCR
```

## 📋 **Documentazione Disponibile**

### 🔧 **Guida Principale ZAI**
- **[Documentazione Completa ZAI Slide Agent](./ZAI_SLIDE_AGENT_DOCUMENTATION.md)**
  - Architettura e configurazione completa
  - Reference API Z.AI
  - Best practices e ottimizzazione
  - Security e monitoring

### 🛠 **Guide per Sviluppatori**
- **[Guida Implementazione ZAI](./ZAI_IMPLEMENTATION_GUIDE.md)**
  - Code examples dettagliati
  - Testing e debugging
  - Performance optimization
  - Deployment considerations

- **[ZAI Quick Reference](./ZAI_QUICK_REFERENCE.md)**
  - Comandi rapidi e template
  - Troubleshooting comune
  - Cost estimation
  - Model selection guide

### ⚙️ **Configurazione**
- **[.env.example](../.env.example)**
  - Template configurazione completo
  - Tutte le variabili d'ambiente
  - Esempi per tutti i provider LLM

## 🎯 **Quick Start**

### 1. Configurazione Base
```bash
# Copia template configurazione
cp .env.example .env

# Modifica con le tue credenziali
nano .env
```

### 2. Avvio Sistema
```bash
# Con Docker (raccomandato)
docker-compose -f docker-compose.optimized.yml up -d

# Verifica stato
docker-compose ps
```

### 3. Test Funzionalità
```bash
# Health check
curl http://localhost:8000/health

# Test ZAI models
curl http://localhost:8000/models

# Test generazione slide
curl -X POST "http://localhost:8000/generate-slides/zai-pdf" \
  -H "Content-Type: application/json" \
  -d '{"topic":"Test AI","num_slides":3,"course_id":"test"}'
```

## 🔌 **Integrazione ZAI**

### Configurazione Raccomandata
```bash
# .env
LLM_TYPE=zai
ZAI_API_KEY=your_api_key_here
ZAI_MODEL=glm-4.5
ZAI_BASE_URL=https://api.z.ai/api/paas/v4/
```

### Modelli Disponibili
| Modello | Uso Ottimale | Costo | Specializzazione |
|---------|---------------|-------|------------------|
| `glm-4.6` | Task complessi | $$ | Flagship con thinking |
| `glm-4.5` | **Slide generation** | $ | **Raccomandato** |
| `glm-4.5-air` | Draft veloci | $ | Economico e veloce |
| `glm-4.5v` | Content con immagini | $$ | Vision capabilities |

### API Endpoints
- `POST /generate-slides/zai-pdf` - Genera PDF completo
- `GET /models` - Lista modelli disponibili
- `GET /health` - Health check sistema

## 📊 **Costi e Performance**

### Slide Generation (glm-4.5)
- **Costo stimato**: ~$0.04 per 10 slide
- **Durata**: 30-60 secondi
- **Linguaggi**: Italiano, Inglese, e altri

### Ottimizzazione Costi
1. Usa `glm-4.5-air` per draft veloci
2. Limita slide a 15-20 per presentazione
3. Implementa caching per richieste ripetute

## 🛡️ **Security e Best Practices**

### API Key Management
```bash
# Never hardcode API keys
ZAI_API_KEY=your_key_here  # ✅ Good
# api_key = "hardcoded"     # ❌ Bad
```

### Input Validation
- Sanitize tutti gli input utente
- Limita numero di slide per richiesta
- Implementa rate limiting

### Monitoring
- Log tutte le chiamate API
- Monitora costi e token usage
- Configura alert per errori

## 🔍 **Troubleshooting Comune**

### "Unknown Model" Error
```bash
# Controlla modello valido
ZAI_MODEL=glm-4.5  # ✅
ZAI_MODEL=glm-4    # ❌ Non valido
```

### Rate Limiting
```python
# Implementa retry con backoff esponenziale
await asyncio.sleep(2 ** attempt)
```

### Performance Lenta
```bash
# Usa modello più veloce
ZAI_MODEL=glm-4.5-air
# O riduci complessità richiesta
```

## 🚀 **Advanced Features**

### RAG Integration
- Indexing automatico documenti
- Semantic search su contenuti
- Context-aware responses

### Background Tasks
- PDF processing asincrono
- OCR per documenti scansionati
- Batch operations

### Multi-Modal
- Supporto immagini (glm-4.5v)
- Document analysis
- Content extraction

## 📁 **Struttura Progetto**

```
tutor-ai/
├── docs/                    # 📚 Documentazione
│   ├── ZAI_SLIDE_AGENT_DOCUMENTATION.md
│   ├── ZAI_IMPLEMENTATION_GUIDE.md
│   └── ZAI_QUICK_REFERENCE.md
├── backend/                 # 🔧 Backend FastAPI
│   ├── services/           # 🧠 Logica di business
│   │   ├── llm_service.py  # ZAI integration
│   │   └── pdf_generator.py
│   ├── main.py             # API endpoints
│   └── .env                # Configurazione
├── frontend/               # 🎨 Frontend Next.js
├── data/                   # 📄 Storage dati
└── docker-compose.optimized.yml
```

## 🤝 **Supporto e Contributi**

### Segnalazione Bug
- Crea issue su GitHub
- Include logs e ambiente
- Fornisci steps per riproduzione

### Richieste Funzionalità
- Apri issue con tag "enhancement"
- Descrivi use case
- Proponi implementazione

### Development Setup
```bash
# Ambiente sviluppo
git clone repository
cd tutor-ai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install
npm run dev
```

## 📞 **Contatti e Risorse**

### Documentazione Ufficiale
- [Z.AI API Reference](https://docs.z.ai/api-reference/agents/agent)
- [Z.AI Slide Generation](https://docs.z.ai/guides/agents/slide)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Next.js Documentation](https://nextjs.org/docs)

### Supporto Interno
- Development Team: Slack #tutor-ai-dev
- Issues: [GitHub Issues](https://github.com/your-org/tutor-ai/issues)
- Documentation: Docs Team

---

## 🏷️ **Metadata**

- **Versione Sistema**: 1.0.0
- **Ultimo Aggiornamento**: 2025-11-03
- **Maintainer**: Tutor-AI Development Team
- **License**: Proprietario

---

*Questa documentazione è un lavoro in corso. Contributi e suggerimenti sono benvenuti!*