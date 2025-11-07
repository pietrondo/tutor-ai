# 🚀 Setup CUDA per GPU Acceleration

## Prerequisiti

1. **NVIDIA Drivers** installati sull'host
2. **Docker NVIDIA Container Toolkit** configurato
3. **GPU NVIDIA** compatibile con CUDA 12.1

## Installazione NVIDIA Container Toolkit

```bash
# Ubuntu/WSL2
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# WSL2 - riavvia WSL dopo l'installazione
wsl --shutdown
```

## Verifica Supporto GPU

### 1. Test NVIDIA Docker

```bash
# Test base container NVIDIA
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
```

Dovresti vedere output simile a:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 545.23.06    Driver Version: 545.23.06    CUDA Version: 12.1     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA RTX 4090     Off  | 00000000:01:00.0 Off |                  N/A |
| 30%   35C    P8    20W / 450W |    446MiB / 24564MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```

### 2. Avvio Tutor-AI con GPU

```bash
# Avvio development con GPU
./start-dev.sh

# O manuale
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 3. Verifica CUDA nell'applicazione

Controlla i logs del backend per vedere:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs backend
```

Dovresti vedere output come:
```
INFO - Using device: cuda
INFO - CUDA device: NVIDIA RTX 4090
INFO - CUDA memory: 24.6GB
INFO - Embedding model loaded successfully device=cuda
```

### 4. Test Performance GPU

Crea un endpoint test per verificare la velocità:

```bash
# Test di embedding su GPU
curl -X POST http://localhost:8000/test-gpu \
  -H "Content-Type: application/json" \
  -d '{"text": "Test di velocità GPU per embedding in italiano"}'
```

## Configurazioni GPU

### Accesso GPU Completo (default)
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

### GPU Specifica
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          device_ids: ['0']
          capabilities: [gpu]
```

### Limite Memoria GPU
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
    limits:
      memory: 8G  # Limita memoria GPU
```

## Troubleshooting

### ❌ "CUDA not available"
**Causa**: NVIDIA Container Toolkit non installato
**Soluzione**: Installa nvidia-docker2

### ❌ "docker run --gpus all: unknown option"
**Causa**: Docker non supporta GPU
**Soluzione**: Installa NVIDIA Container Toolkit

### ❌ "Could not load CUDA runtime"
**Causa**: Drivers NVIDIA non compatibili
**Soluzione**: Aggiorna drivers NVIDIA

### ❌ "Out of memory"
**Causa**: GPU memory insufficiente
**Soluzione**: Limita memoria GPU o usa CPU

### ❌ "Container stuck at build"
**Causa**: Download CUDA runtime lungo
**Soluzione**: Attendi download prima volta (~2GB)

## Performance Expectations

| Operazione | CPU (8-core) | GPU (RTX 4090) | Speedup |
|------------|--------------|----------------|---------|
| Embedding 1000 docs | ~45s | ~3s | **15x** |
| Semantic search | ~2s | ~0.1s | **20x** |
| Batch processing | ~2min | ~8s | **15x** |

## Monitoraggio GPU

```bash
# Monitoraggio GPU durante l'uso
nvidia-smi -l 1

# Logs con statistiche GPU
docker-compose logs backend | grep -E "(CUDA|GPU|device)"
```

## Fallback CPU

Se CUDA non è disponibile, l'applicazione tornerà automaticamente a CPU:

```
INFO - Using device: cpu
WARNING - CUDA not available, falling back to CPU
INFO - Embedding model loaded successfully device=cpu
```

## Tips Ottimizzazione

1. **Warm-up GPU**: Carica il modello all'avvio
2. **Batch processing**: Processa più documenti insieme
3. **Memory management**: Pulisci cache GPU periodicamente
4. **Monitor usage**: Controlla utilizzo GPU durante indicizzazione

Ora hai **GPU acceleration completa** per indicizzazione e embedding! 🚀