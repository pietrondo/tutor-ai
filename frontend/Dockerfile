FROM node:20-alpine AS builder

# Imposta la directory di lavoro
WORKDIR /app

# Copia solo package files per cache effectiveness
COPY package*.json ./

# Installa tutte le dipendenze (incluse quelle di dev)
RUN npm install

# Copia il codice sorgente
COPY . .

# Build della applicazione
RUN npm run build

# Stage di produzione
FROM node:20-alpine AS production

# Imposta la directory di lavoro
WORKDIR /app

# Copia package files e node_modules dal builder
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules

# Copia il codice sorgente
COPY . .

# Copia i file di build dal builder
COPY --from=builder /app/.next ./.next

# Espone la porta
EXPOSE 3000

# Comando per avviare l'applicazione
CMD ["npm", "start"]