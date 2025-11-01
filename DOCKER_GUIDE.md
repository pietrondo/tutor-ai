# Guida Docker Ottimizzata per Tutor AI (WSL2/Linux)

Questa guida descrive come utilizzare gli script Docker ottimizzati per il progetto Tutor AI in ambiente WSL2/Linux, con particolare attenzione alle performance e al caching.

## 📋 Indice

- [Panoramica](#panoramica)
- [Prerequisiti](#prerequisiti)
- [Struttura Scripts](#struttura-scripts)
- [Utilizzo Rapido](#utilizzo-rapido)
- [Configurazione WSL2](#configurazione-wsl2)
- [Ottimizzazioni Performance](#ottimizzazioni-performance)
- [Troubleshooting](#troubleshooting)
- [Riferimento Comandi](#riferimento-comandi)

## 🎯 Panoramica

Il progetto include 4 script Docker ottimizzati:

1. **`docker-build.sh`** - Building con cache avanzata
2. **`docker-start.sh`** - Avvio intelligente con health check
3. **`docker-stop.sh`** - Arresto graceful e cleanup
4. **`docker-logs.sh`** - Visualizzazione logs avanzata

### ✅ Caratteristiche Principali

- **Cache Ottimizzata**: Riutilizzo dependencies Python/Node.js
- **Build Parallelo**: Backend e frontend contemporaneamente
- **Health Check**: Verifica automatica servizi
- **WSL2 Ready**: Ottimizzato per ambiente Windows Subsystem for Linux
- **Gestione Errori**: Robusta error handling e recovery
- **Logging Dettagliato**: Output colorato e informativo

## 🔧 Prerequisiti

### Docker Engine
```bash
# Installazione Docker (Ubuntu/WSL2)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Riavvia o esegui logout/login
newgrp docker
```

### Docker Compose
```bash
# Docker Compose V2 (incluso in Docker Desktop o installabile separatamente)
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

### WSL2 Configurazione
```bash
# File: ~/.wslconfig (in Windows)
[wsl2]
memory=4GB
processors=2
swap=2GB
localhostForwarding=true
```

## 📁 Struttura Scripts

```
tutor-ai/
├── docker-build.sh      # Build ottimizzato con cache
├── docker-start.sh      # Avvio intelligente servizi
├── docker-stop.sh       # Arresto graceful e cleanup
├── docker-logs.sh       # Visualizzazione logs avanzata
├── docker-compose.yml   # Configurazione servizi
├── backend/
│   └── Dockerfile       # Backend Python/FastAPI
└── frontend/
    └── Dockerfile       # Frontend Next.js
```

## 🚀 Utilizzo Rapido

### Primo Avvio
```bash
# 1. Build delle immagini
./docker-build.sh

# 2. Avvio dei servizi
./docker-start.sh

# 3. Verifica status
./docker-start.sh --check
```

### Utilizzo Giornaliero
```bash
# Avvio rapido (se già buildato)
./docker-start.sh

# Visualizzazione logs
./docker-logs.sh -f

# Arresto servizi
./docker-stop.sh
```

### Sviluppo
```bash
# Build + avvio
./docker-start.sh --build

# Riavvio completo
./docker-start.sh --restart

# Logs solo backend
./docker-logs.sh -f backend
```

## ⚙️ Configurazione WSL2

### Ottimizzazione Memoria
```bash
# File: ~/.wslconfig (in Windows C:\Users\TuoUtente\.wslconfig)
[wsl2]
memory=6GB                    # Aumenta memoria per Docker
processors=4                  # CPU cores
swap=4GB                      # Swap file size
localhostForwarding=true      # Forwarding porte
```

### Networking
```bash
# In ~/.bashrc o ~/.zshrc
export DOCKER_HOST="unix:///var/run/docker.sock"
export COMPOSE_PROJECT_NAME="tutor-ai"
```

### Performance Filesystem
```bash
# Montaggio project directory in /mnt/c/ (già default in WSL2)
# Evitare di usare filesystem WSL2 (/home/) per progetti grandi
```

## 🏎️ Ottimizzazioni Performance

### Cache Strategy

#### Python Dependencies Cache
```dockerfile
# backend/Dockerfile ottimizzato
FROM python:3.11-slim

# System dependencies in layer separato
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Python dependencies con cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

#### Node.js Dependencies Cache
```dockerfile
# frontend/Dockerfile ottimizzato
FROM node:20-alpine

# Cache package.json per npm cache effectiveness
COPY package*.json ./
RUN npm ci --only=production --silent && npm cache clean --force
```

### BuildKit Optimization
```bash
# Docker BuildKit automatico negli script
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

### Volume Mounting Strategy
```yaml
# docker-compose.yml ottimizzato
services:
  frontend:
    volumes:
      - ./frontend:/app              # Source code hot-reload
      - /app/node_modules            # Evita sovrascrittura node_modules
      - /app/.next                   # Cache Next.js build
```

## 🔍 Troubleshooting

### Problemi Comuni

#### 1. Docker daemon non running
```bash
# Errore: "Cannot connect to the Docker daemon"
sudo systemctl start docker
sudo systemctl enable docker
```

#### 2. Porte già in uso
```bash
# Controlla porte utilizzate
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Uccidi processi
sudo fuser -k 3000/tcp
sudo fuser -k 8000/tcp
```

#### 3. Build lento su WSL2
```bash
# Controlla configurazione WSL2
cat ~/.wslconfig

# Aumenta memoria se necessario
# Riavvia WSL2 da PowerShell: wsl --shutdown
```

#### 4. Cache non utilizzata
```bash
# Pulisci cache Docker se necessario
docker builder prune -a

# Forza rebuild senza cache
./docker-build.sh --no-cache
```

#### 5. Container non parte
```bash
# Controlla logs
./docker-logs.sh

# Verifica immagini
docker images | grep tutor-ai

# Riavvio completo
./docker-start.sh --restart --build
```

### Debug Mode
```bash
# Output dettagliato
./docker-start.sh --verbose

# Logs con timestamp
./docker-logs.sh --since 1h

# Export logs per analisi
./docker-logs.sh --export
```

## 📖 Riferimento Comandi

### docker-build.sh
```bash
./docker-build.sh [OPZIONI]

Opzioni:
  -h, --help     Mostra help
  -c, --cleanup  Pulizia Docker
  -b, --backend  Solo backend
  -f, --frontend Solo frontend
  -p, --parallel Build parallelo (default)
  --no-cache     Build senza cache
  --force        Force rebuild completo
```

### docker-start.sh
```bash
./docker-start.sh [OPZIONI]

Opzioni:
  -h, --help      Mostra help
  -r, --restart   Riavvio completo
  -b, --build     Build + avvio
  -c, --check     Solo verifica status
  -v, --verbose   Output dettagliato
  --no-health     Salta health check
```

### docker-stop.sh
```bash
./docker-stop.sh [OPZIONI] [SERVIZIO]

Opzioni:
  -h, --help      Mostra help
  -c, --cleanup   Cleanup completo
  -f, --force     Forza arresto

Servizi:
  backend         Solo backend
  frontend        Solo frontend
  redis           Solo redis
```

### docker-logs.sh
```bash
./docker-logs.sh [OPZIONI] [SERVIZIO]

Opzioni:
  -h, --help      Mostra help
  -f, --follow    Follow mode
  -t, --tail N    Ultime N righe
  -e, --export    Export su file
  -a, --all       Tutti i servizi
  --since TIME    Da tempo specificato
  --until TIME    Fino a tempo specificato
```

## 📊 Performance Tips

### 1. Cache Management
```bash
# Controlla dimensione cache
docker system df

# Pulisci se necessario
docker system prune -a
```

### 2. Monitoraggio Risorse
```bash
# Container resource usage
docker stats

# Disk usage
docker system du
```

### 3. Development Workflow
```bash
# Per sviluppo con hot-reload
./docker-start.sh  # Solo una volta

# Modifiche al codice si riflettono automaticamente
# Frontend: hot-reload su http://localhost:3000
# Backend: auto-reload su http://localhost:8000
```

### 4. Production Build
```bash
# Build ottimizzato per produzione
./docker-build.sh --force

# Senza volumi di sviluppo
# Modificare docker-compose.yml per rimuovere volume mounts
```

## 🔄 Workflow Consigliato

### Sviluppo Locale
```bash
# 1. Setup iniziale
./docker-build.sh

# 2. Avvio giornaliero
./docker-start.sh

# 3. Durante sviluppo
./docker-logs.sh -f  # Monitoraggio logs

# 4. Fine giornata
./docker-stop.sh
```

### Aggiornamento Dipendenze
```bash
# 1. Aggiorna requirements.txt o package.json
# 2. Force rebuild
./docker-build.sh --force
./docker-start.sh --restart
```

### Debug Issues
```bash
# 1. Verifica status
./docker-start.sh --check

# 2. Controlla logs recenti
./docker-logs.sh --since 30m

# 3. Riavvio completo se necessario
./docker-start.sh --restart --build
```

---

## 🆘 Supporto

Per problemi o domande:

1. Controllare [Troubleshooting](#troubleshooting)
2. Verificare logs con `./docker-logs.sh`
3. Controllare configurazione WSL2
4. Riavviare Docker daemon se necessario

**Note**: Gli script sono ottimizzati per WSL2 ma funzionano anche su Linux nativo.