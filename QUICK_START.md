# 🚀 Avvio Rapido - Tutor AI

## Setup in 2 Minuti

### 1. Clone e Setup
```bash
git clone <repository-url>
cd tutor-ai
chmod +x setup.sh
./setup.sh
```

### 2. Configura API Key
Edita `backend/.env`:
```env
# Per OpenAI
LLM_TYPE=openai
OPENAI_API_KEY=sk-tua-chiave

# Per Ollama (locale)
LLM_TYPE=local
LOCAL_LLM_URL=http://localhost:11434/v1
```

### 3. Avvia le Applicazioni
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 4. Apri il Browser
Vai su http://localhost:3000

## ✅ Pronto!

Ora puoi:
- 📚 Creare corsi universitari
- 📄 Caricare PDF e materiali
- 🤖 Chattare con il tutor AI
- 📊 Tracciare i progressi
- 🧠 Generare quiz automatici

## Docker Setup (Alternativa)

```bash
docker-compose up -d
```

Visita http://localhost:3000

---

**Buono studio! 🎓✨**