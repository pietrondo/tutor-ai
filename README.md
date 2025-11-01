# 🎓 Tutor AI - Sistema di Apprendimento Intelligente

Una piattaforma completa di tutoring AI per corsi universitari con RAG (Retrieval-Augmented Generation) locale, che permette di caricare materiali di studio, fare chat con un tutor AI, tracciare i progressi e generare quiz personalizzati.

## ✨ Caratteristiche Principali

- 🤖 **Tutor AI Intelligente**: Chat basata su OpenAI GPT-4o o modelli locali (Ollama/LM Studio)
- 📚 **Gestione Corsi**: Organizza i materiali per corso universitario
- 📄 **Elaborazione PDF**: Caricamento e indicizzazione automatica di documenti PDF
- 🔍 **RAG System**: Retrieval-Augmented Generation per risposte basate sui tuoi materiali
- 📊 **Tracciamento Progressi**: Monitora sessioni di studio, tempo dedicato e argomenti coperti
- 🧠 **Quiz Generati AI**: Crea test personalizzati basati sui materiali del corso
- 🎯 **Studio Guidato**: Piano di studio personalizzato e suggerimenti di apprendimento
- 🌐 **Interfaccia Moderna**: Frontend React/Next.js responsive e intuitiva

## 🏗️ Architettura

```
tutor-ai/
├── backend/                 # Backend FastAPI
│   ├── services/           # Servizi principali
│   │   ├── rag_service.py      # Sistema RAG con ChromaDB
│   │   ├── llm_service.py      # Integrazione LLM (OpenAI/Local)
│   │   ├── course_service.py   # Gestione corsi
│   │   └── study_tracker.py    # Tracciamento progressi
│   ├── main.py             # API endpoints
│   └── requirements.txt    # Dipendenze Python
├── frontend/               # Frontend Next.js
│   ├── src/
│   │   ├── app/           # Pagine dell'applicazione
│   │   └── components/    # Componenti React
│   └── package.json       # Dipendenze Node.js
└── data/                   # Dati locali
    ├── courses/           # Corsi e materiali
    ├── vector_db/         # Database vettoriale ChromaDB
    └── tracking/          # Dati di progressi
```

## 🚀 Setup Rapido

### Prerequisiti

- Python 3.8+
- Node.js 18+
- Account OpenAI (opzionale, supportati anche LLM locali)

### 1. Clona il Repository

```bash
git clone <repository-url>
cd tutor-ai
```

### 2. Setup Backend

```bash
cd backend

# Crea ambiente virtuale
python -m venv venv

# Attiva ambiente
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Configura le variabili d'ambiente
cp .env.example .env
```

### 3. Configura le Credenziali

Modifica il file `.env` nel backend:

```env
# Scegli tra OpenAI o LLM locale
LLM_TYPE=openai

# Opzione 1: OpenAI
OPENAI_API_KEY=la_tua_chiave_api
OPENAI_MODEL=gpt-4o

# Opzione 2: LLM Locale (Ollama)
# LLM_TYPE=local
# LOCAL_LLM_URL=http://localhost:11434/v1
# LOCAL_LLM_MODEL=llama3.1
```

### 4. Setup Frontend

```bash
cd frontend

# Installa dipendenze
npm install

# Oppure con yarn
yarn install
```

### 5. Avvia le Applicazioni

In due terminali separati:

```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

L'applicazione sarà disponibile su:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## 🔧 Configurazione Dettagliata

### OpenAI Setup

1. Vai su [OpenAI Platform](https://platform.openai.com/)
2. Crea un account e ottieni la tua API key
3. Aggiungi la key nel file `.env`

### LLM Locale (Ollama)

1. Installa Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
2. Scarica un modello: `ollama pull llama3.1`
3. Configura le variabili d'ambiente nel file `.env`

### LM Studio Setup

1. Scarica e installa LM Studio
2. Carica un modello LLM
3. Avvia il server locale (di solito su http://localhost:1234)
4. Configura l'URL nel file `.env`

## 📖 Guida all'Uso

### 1. Creare un Corso

1. Vai sulla homepage
2. Clicca "Nuovo Corso"
3. Inserisci nome, descrizione e materia
4. Salva il corso

### 2. Caricare Materiali

1. Seleziona il corso creato
2. Vai alla sezione "Materiali del Corso"
3. Trascina i file PDF o clicca per selezionarli
4. Attendi l'indicizzazione automatica

### 3. Chattare con il Tutor AI

1. Seleziona un corso con materiali caricati
2. Clicca "Chat con Tutor"
3. Fai domande sui contenuti del corso
4. Il tutor risponderà basandosi sui tuoi materiali

### 4. Monitorare Progressi

1. Vai su "Progressi di Studio" nel corso
2. Visualizza sessioni, tempo di studio, argomenti coperti
3. Controlla le serie giornaliere di studio

### 5. Creare Quiz

1. Clicca "Crea Quiz" nel corso
2. Scegli argomento e difficoltà
3. Il sistema genererà domande basate sui materiali
4. Rispondi e verifica le tue conoscenze

## 🛠️ Sviluppo

### Struttura dei Servizi

- **RAGService**: Gestisce l'indicizzazione e retrieval dei documenti
- **LLMService**: Interfaccia per OpenAI API e LLM locali
- **CourseService**: CRUD per corsi e materiali
- **StudyTracker**: Tracciamento sessioni e analisi dei progressi

### API Endpoints

```
GET  /courses                    # Lista tutti i corsi
POST /courses                    # Crea nuovo corso
GET  /courses/{id}               # Dettagli corso
POST /courses/{id}/upload        # Carica materiali
POST /chat                       # Chat con tutor AI
POST /quiz                       # Genera quiz
GET  /study-progress/{id}        # Progressi corso
GET  /study-insights/{id}        # Analisi dettagliata
```

### Estensioni Possibili

- Integrazione con altri formati di documenti (DOCX, PPT)
- Sistema di flashcard e ripetizione spaziata
- Condivisione di corsi tra utenti
- Integrazione con calendar per pianificazione studio
- Dashboard admin per gestione multiutente

## 🐛 Troubleshooting

### Problemi Comuni

**Errore connessione OpenAI**:
- Verifica la API key nel file `.env`
- Controlla la connessione internet
- Verifica il credito disponibile sull'account OpenAI

**LLM locale non risponde**:
- Assicurati che Ollama/LM Studio sia in esecuzione
- Verifica l'URL nel file `.env`
- Controlla che il modello sia caricato correttamente

**PDF non viene indicizzato**:
- Verifica che il file sia un PDF valido
- Controlla i log del backend per errori specifici
- Prova a riavviare il backend

**Frontend non si connette al backend**:
- Assicurati che il backend sia in esecuzione su porta 8000
- Verifica che non ci siano firewall bloccanti
- Controlla i log del browser per errori CORS

## 📄 Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi il file LICENSE per dettagli.

## 🤝 Contributi

I contributi sono benvenuti! Si prega di:

1. Fare fork del repository
2. Creare una feature branch
3. Commit delle modifiche
4. Push al branch
5. Aprire una Pull Request

## 📞 Supporto

Per domande o problemi:

- Apri una issue su GitHub
- Contatta lo sviluppatore
- Consulta la documentazione tecnica

---

**Tutor AI** - Il tuo compagno di studio intelligente per l'università! 🎓✨