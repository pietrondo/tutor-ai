# 🚀 Guida allo Sviluppo Ottimizzato

## Setup Sviluppo Zero-Rebuild

Questa configurazione elimina completamente i rebuild Docker durante lo sviluppo grazie ai bind mount e hot reload.

### Avvio Sviluppo

```bash
# Metodo 1: Script automatico (consigliato)
./start-dev.sh

# Metodo 2: Manuale
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Comandi Utili

```bash
# Avvio in background
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Visualizza logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# Stop servizi
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Riavvio singolo servizio
docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart backend
```

### 🎯 Vantaggi delle Ottimizzazioni

#### **1. Zero Rebuild per Codice**
- Modifichi un file Python ✅ Si aggiorna istantaneamente
- Modifichi un file TypeScript ✅ Hot reload automatico
- Nessun attesa per rebuild Docker

#### **2. Cache Intelligente**
- Pacchetti apt salvati in volumi persistenti
- Cache pip condivisa tra i rebuild
- BuildKit mounts per performance massime

#### **3. Copia Selettiva**
- Solo i file necessari vengono copiati
- Ordine ottimizzato per caching layer
- Context build minimizzato

### 📁 Struttura File

```
tutor-ai/
├── docker-compose.yml           # Configurazione base
├── docker-compose.dev.yml       # Override development
├── backend/
│   ├── Dockerfile              # Ottimizzato con copia selettiva
│   └── .dockerignore           # Context minimizzato
├── frontend/
│   ├── Dockerfile              # Multi-stage build
│   └── .dockerignore
├── start-dev.sh                # Script avvio sviluppo
└── DEV_GUIDE.md               # Questa guida
```

### 🔧 Hot Reload Configurazioni

#### **Backend (FastAPI)**
- `--reload`: Watch file Python
- `--reload-dir /app`: Directory specifica
- `--reload-exclude`: Esclude cache Python

#### **Frontend (Next.js)**
- Bind mount del codice sorgente
- Node modules preservato
- Cache Next.js ottimizzata

### 🏗️ Production Build

Per deploy in production:

```bash
# Build production
docker-compose -f docker-compose.yml build

# Avvio production
docker-compose -f docker-compose.yml up
```

### 🐛 Troubleshooting

#### **Problemi comuni:**

1. **Permission denied su start-dev.sh**
   ```bash
   chmod +x start-dev.sh
   ```

2. **Bind mount sovrascrive dipendenze**
   - I volumi apt cache sono separati e protetti
   - Python venv non viene sovrascritto

3. **Hot reload non funziona**
   - Controlla che il file sia nella directory montata
   - Verifica log per errori di watchdog

4. **Build lento la prima volta**
   - Normale, scarica tutte le dipendenze
   - I rebuild successivi saranno rapidissimi

### 📊 Performance

| Operazione | Prima | Dopo |
|------------|--------|------|
| Modifica file Python | ~30s rebuild | <1s hot reload |
| Modifica file TS | ~20s rebuild | <1s hot reload |
| Cambio requirements.txt | ~2min reinstall | ~2min (stesso) |
| Cambio system packages | ~3min reinstall | ~10s con cache |

### 🔄 Workflow Sviluppo

1. **Start**: `./start-dev.sh`
2. **Modifica codice**: ✅ Si aggiunge automaticamente
3. **Test**: http://localhost:8000/docs
4. **Stop**: `Ctrl+C`

**Nessun rebuild Docker necessario durante lo sviluppo!** 🎉