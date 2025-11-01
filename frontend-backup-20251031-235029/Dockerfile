FROM node:18-alpine

# Imposta la directory di lavoro
WORKDIR /app

# Copia package files
COPY package*.json ./

# Installa dipendenze
RUN npm ci

# Copia il codice sorgente
COPY . .

# Build della applicazione
RUN npm run build

# Espone la porta
EXPOSE 3000

# Comando per avviare l'applicazione
CMD ["npm", "start"]