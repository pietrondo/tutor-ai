# 🐳 Docker Quick Start - Tutor AI

Guida rapida per avviare il progetto Tutor AI con Docker ottimizzato per WSL2/Linux.

## 🚀 Avvio Rapido (2 minuti)

```bash
# 1. Build delle immagini Docker
./docker-build.sh

# 2. Avvio tutti i servizi
./docker-start.sh

# 3. Accedi alle applicazioni
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 📋 Prerequisiti

- Docker Engine installato
- Docker Compose V2
- WSL2 (se su Windows) o Linux

## 🛠️ Comandi Essenziali

```bash
# Avvio servizi
./docker-start.sh

# Riavvio completo
./docker-start.sh --restart

# Visualizza logs in tempo reale
./docker-logs.sh -f

# Arresta servizi
./docker-stop.sh

# Solo status
./docker-start.sh --check
```

## 🔧 Sviluppo

```bash
# Build + avvio (per modifiche Dockerfile)
./docker-start.sh --build

# Logs solo backend
./docker-logs.sh -f backend

# Logs solo frontend
./docker-logs.sh -f frontend
```

## 🧹 Pulizia

```bash
# Rimuovi container e immagini
./docker-stop.sh --cleanup

# Rebuild completo
./docker-build.sh --force
```

## ❓ Problemi Comuni

**Docker non parte:**
```bash
sudo systemctl start docker
```

**Porte occupate:**
```bash
sudo fuser -k 3000/tcp 8000/tcp 6379/tcp
```

**Build lento WSL2:**
```bash
# Aumenta memoria in ~/.wslconfig
wsl --shutdown  # da PowerShell Windows
```

## 📖 Documentazione Completa

Vedi [`DOCKER_GUIDE.md`](./DOCKER_GUIDE.md) per guida dettagliata e troubleshooting.

---

**Nota**: Gli script utilizzano cache avanzata per evitare download ripetuti di dependencies (Python packages, Node.js modules).