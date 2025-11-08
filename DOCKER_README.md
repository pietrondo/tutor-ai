# 🐳 Tutor-AI Docker - Guida Rapida

## 🚀 Avvio Rapido (Sistema Semplificato)

**UN SOLO COMANDO per avviare tutto:**

```bash
./start.sh
```

Questo comando automaticamente:
- ✅ Verifica Docker
- ✅ Crea directory necessarie
- ✅ Genera file .env se mancante
- ✅ Build immagini Docker (se necessario)
- ✅ Avvia tutti i servizi
- ✅ Health check automatico
- ✅ Mostra URL di accesso

## 📋 Comandi Disponibili

```bash
# Modalità sviluppo (default) - con hot reload
./start.sh dev

# Modalità semplificata - configurazione base
./start.sh simple

# Modalità produzione - ottimizzata
./start.sh prod

# Gestione servizi
./start.sh stop      # Arresta tutti i servizi
./start.sh logs      # Mostra log in tempo reale
./start.sh status    # Stato dei container
./start.sh clean     # Pulizia completa container/immagini
```

## 🌐 URL di Accesso

Dopo l'avvio, i servizi saranno disponibili a:

- **Frontend**: http://localhost:5000 (modalità dev) o http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentazione API**: http://localhost:8000/docs
- **Redis**: localhost:6379

## ⚙️ Configurazione

### File .env
Il file `backend/.env` viene creato automaticamente al primo avvio:

```env
# Tutor-AI Environment Configuration
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=debug

# API Configuration (da configurare)
OPENAI_API_KEY=your_openai_key_here
ZAI_API_KEY=your_zai_key_here

# Database
REDIS_URL=redis://redis:6379
DATABASE_URL=sqlite:///./data/app.db

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000,http://127.0.0.1:5000
```

**IMPORTANTE**: Configura le tue API keys per funzionalità complete!

### Directory Automatiche
Vengono create automaticamente:
- `data/uploads/` - File caricati
- `data/vector_db/` - Database vettoriale
- `data/courses/` - Dati corsi
- `data/chat_sessions/` - Sessioni chat
- `logs/` - Log applicativi

## 🏗️ Architettura Docker

### Modalità Sviluppo (`dev`)
- **Hot Reload**: Modifiche al codice si applicano automaticamente
- **Bind Mount**: Codice montato direttamente nei container
- **Debug**: Logging dettagliato e variabili di sviluppo
- **Performance**: Ottimizzato per sviluppo rapido

### Modalità Semplificata (`simple`)
- **Setup Minimo**: Configurazione base essenziale
- **Risorse Ridotte**: Utilizzo minimo di memoria/CPU
- **Avvio Veloce**: Ideale per test rapidi

### Modalità Produzione (`prod`)
- **Ottimizzata**: Build multi-stage e caching
- **Sicurezza**: Environment di produzione
- **Performance**: Ottimizzazioni per carichi di lavoro reali
- **Stabilità**: Health check e restart automatici

## 🔄 Vecchi Script (Deprecati)

Gli script Docker precedenti sono stati spostati in `scripts/docker/`:
- `scripts/docker/start-dev.sh` - Sviluppo legacy
- `scripts/docker/docker-start.sh` - Avvio avanzato
- `scripts/docker/docker-build.sh` - Build script
- `scripts/docker/docker-stop.sh` - Stop script
- `scripts/docker/docker-logs.sh` - Logs script
- `scripts/docker/backup-smart.sh` - Backup script

**Nota**: Utilizzare `./start.sh` invece degli script legacy.

## 🐛 Troubleshooting

### Docker non parte
```bash
# Verifica Docker
docker --version
docker-compose --version
docker info
```

### Porte già in uso
```bash
# Controlla porte occupate
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Pulisci container
./start.sh clean
```

### Build fallita
```bash
# Pulisci e rebuild
./start.sh clean
./start.sh dev
```

### Permesso negato
```bash
# Rendi eseguibile
chmod +x start.sh
```

### Backend non risponde
```bash
# Controlla log
./start.sh logs

# Verifica container
docker ps
docker logs tutor-ai-backend
```

## 💡 Suggerimenti

1. **Primo avvio**: Usa `./start.sh dev` per sviluppo con hot reload
2. **Presentazioni**: Usa `./start.sh simple` per avvio rapido
3. **Produzione**: Usa `./start.sh prod` per massima performance
4. **Sviluppo frontend**: In modalità `dev`, le modifiche React si applicano automaticamente
5. **Sviluppo backend**: In modalità `dev`, le modifiche Python si applicano automaticamente

## 📚 Riferimenti

- **Documentazione completa**: `CLAUDE.md`
- **Roadmap CLE**: `COGNITIVE_LEARNING_ROADMAP.md`
- **Setup locale**: `LOCAL_SETUP_SUMMARY.md`

---

**Tutor-AI Cognitive Learning Engine** 🧠
*Last updated: 2025-11-08*