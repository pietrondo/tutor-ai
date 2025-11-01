FROM node:20-alpine

# Imposta la directory di lavoro
WORKDIR /app

# Copia solo package files per cache effectiveness
COPY package*.json ./

# Installa dipendenze con cache ottimizzata
RUN npm ci --only=production --silent && npm cache clean --force

# Copia il codice sorgente
COPY . .

# Build della applicazione
RUN npm run build

# Espone la porta
EXPOSE 3000

# Comando per avviare l'applicazione
CMD ["npm", "start"]