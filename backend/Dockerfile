FROM python:3.11-slim

# Imposta la directory di lavoro
WORKDIR /app

# Installa dipendenze di sistema in un layer separato per caching
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Copia requirements e installa dipendenze Python con ottimizzazioni
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# Copia il codice dell'applicazione
COPY . .

# Crea le directory necessarie
RUN mkdir -p data/{courses,vector_db,uploads,tracking}

# Espone la porta
EXPOSE 8000

# Comando per avviare l'applicazione
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]