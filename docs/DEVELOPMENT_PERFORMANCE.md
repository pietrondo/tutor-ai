# Development Performance Guide

## 🎯 Overview

Tutor-AI includes comprehensive development performance optimizations to address INP (Interaction to Next Paint) issues and provide a smooth development experience.

## 🚀 Mode di Sviluppo

### 1. Modalità Standard Development
```bash
./start.sh dev
```
- ✅ Hot reload con ottimizzazioni INP
- ✅ Memory management migliorato (4GB heap)
- ✅ Webpack splitting per cache ottimale
- ✅ Performance monitoring integrato

### 2. Modalità Turbo (Sperimentale)
```bash
npm run dev:turbo  # o nel container: docker-compose exec frontend npm run dev:turbo
```
- ⚡ Utilizza Turbopack per build più veloci
- 🔄 Hot reload ottimizzato
- ⚠️ Sperimentale - potrebbe avere instabilità

### 3. Modalità Fast Development
```bash
npm run dev:fast  # già configurato in docker-compose.dev.yml
```
- 🚀 NODE_OPTIONS='--max-old-space-size=4096'
- ⚡ Build workers limitati a 1 per ridurre contention
- 🎯 Ottimizzato per development experience

### 4. Modalità Produzione (Zero Compilazione)
```bash
./start.sh prod
```
- 🔥 **PREVIENE COMPLETAMENTE LA COMPILAZIONE CONTINUA**
- ✅ Usa build standalone pre-compilata
- ✅ Esegue `node server.js` invece di `npm run dev`
- ✅ Performance ottimali, nessun hot reload

## 🛠️ Ottimizzazioni Implementate

### Next.js Configuration
```javascript
// next.config.js
experimental: {
  optimizeCss: true,
  optimizePackageImports: ['lucide-react', '@heroicons/react'],
},
```

### Webpack Development Optimizations
- **SplitChunks**: Vendor e common chunks separati
- **Minimal Stats**: Riduce overhead di analisi
- **Cache Groups**: Ottimizzazione caching bundle

### React Performance Hooks
- **useDebounce**: Previne chiamate API eccessive
- **useThrottle**: Ottimizza event handlers ad alta frequenza
- **useIntersectionObserver**: Lazy loading ottimizzato
- **useDevPerformanceMonitor**: Monitoring performance in development

### Memory Management
- **4GB Heap**: `NODE_OPTIONS='--max-old-space-size=4096'`
- **Build Workers**: Limitati a 1 per ridurre contention
- **Volume Caching**: Docker volumes per node_modules e .next cache

## 📊 Troubleshooting Performance

### Problema: INP > 50ms in Development
**Sintomi**: Interfaccia lenta, input lag
**Soluzioni**:
1. Usa `./start.sh dev` (già ottimizzato)
2. Chiudi altre applicazioni pesanti
3. Aumenta memoria Docker: `docker stats`
4. Usa `npm run dev:fast` per ancora più memoria

### Problema: Memory > 2GB in Development
**Sintomi**: Container out of memory
**Soluzioni**:
1. Verifica Docker memory allocation (min 4GB)
2. Usa `docker system prune` per pulire cache
3. Riavvia container: `./start.sh stop && ./start.sh dev`

### Problema: Hot Reload Lento
**Sintomi**: Modifiche richiedono > 5 secondi
**Soluzioni**:
1. Usa modalità Turbo: `npm run dev:turbo`
2. Verifica file watching non eccessivo
3. Controlla volume mounts in docker-compose.dev.yml

## 🔧 Debug Performance

### 1. Monitoring React Components
```typescript
import { useDevPerformanceMonitor } from '@/lib/dev-performance'

function MyComponent() {
  useDevPerformanceMonitor('MyComponent');
  // ...component code
}
```

### 2. Chrome DevTools
- **Performance Tab**: Registra interazioni utente
- **Memory Tab**: Monitora heap usage
- **Network Tab**: Verifica richieste API lente

### 3. Docker Monitoring
```bash
# Monitora risorse container
docker stats

# Logs performance
docker-compose logs frontend | grep -i performance
```

## 🎛️ Environment Variables per Performance

### Development
```bash
NODE_ENV=development
NEXT_TELEMETRY_DISABLED=1
NODE_OPTIONS=--max-old-space-size=4096
NEXT_BUILD_WORKERS=1
```

### Produzione
```bash
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
# Nessuna variabile speciale necessaria
```

## 📈 Benchmark Results

### Modalità Development (Ottimizzata)
- **INP**: ~20-30ms (migliorato da 90ms)
- **First Load**: ~1-2s
- **Hot Reload**: ~2-3s
- **Memory Usage**: ~1.5-2GB

### Modalità Produzione
- **INP**: ~5-10ms (ottimale)
- **First Load**: ~800ms-1.5s
- **No Hot Reload**: N/A
- **Memory Usage**: ~500MB-1GB

## 🚨 Best Practices

### Sviluppo
1. **Usa sempre** `./start.sh dev` per sviluppo
2. **Monitora** INP con Chrome DevTools
3. **Chiudi** tabs/finestre non necessarie
4. **Riavvia** container periodicamente

### Produzione
1. **Usa sempre** `./start.sh prod` per test performance
2. **Nessuna** compilazione continua prevista
3. **Monitora** memoria in produzione
4. **Usa** build ottimizzate per deployment

## 🔗 Links Utili

- [React Performance](https://react.dev/learn/render-and-commit)
- [Next.js Performance](https://nextjs.org/docs/advanced-features/measuring-performance)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance)
- [Docker Performance Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

*Aggiornato: 2025-11-11*