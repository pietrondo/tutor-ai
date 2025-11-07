# Multi-stage build ottimizzato per Next.js
FROM node:20-alpine AS base

# Installa dipendenze base per Alpine
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copia package files con lockfile ottimizzato
COPY package.json package-lock.json* ./

# Stage di installazione dipendenze
FROM base AS deps

# Imposta npm registry per performance
RUN npm config set registry https://registry.npmjs.org/ && \
    npm config set fetch-timeout 60000

# Installa dipendenze con cache ottimizzato
RUN --mount=type=cache,target=/root/.npm \
    npm ci --include=dev --silent

# Stage di sviluppo
FROM base AS development

# Installa dipendenze con cache
RUN --mount=type=cache,target=/root/.npm \
    npm ci --include=dev --silent

# Copia il codice sorgente
COPY . .

# Espone la porta per development
EXPOSE 3000

# Imposta variabili ambiente sviluppo
ENV NODE_ENV development
ENV NEXT_TELEMETRY_DISABLED 1
ENV PORT 3000
ENV HOSTNAME 0.0.0.0

# Comando per development server
CMD ["npm", "run", "dev"]

# Stage di build
FROM base AS builder

# Copia le dipendenze dal stage deps
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/package.json ./package.json

# Copia il resto del codice sorgente
COPY . .

# Imposta variabili ambiente per build ottimizzata
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV production

# Build dell'applicazione con standalone output
RUN npm run build

# Stage di produzione leggero
FROM node:20-alpine AS runner

WORKDIR /app

# Crea utente non-root per sicurezza
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copia i file di build standalone (includes required node_modules)
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Copia public folder
COPY --from=builder /app/public ./public

# Imposta utente non-root
USER nextjs

# Espone la porta
EXPOSE 3000

# Imposta variabili ambiente produzione
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Comando ottimizzato per produzione
CMD ["node", "server.js"]
