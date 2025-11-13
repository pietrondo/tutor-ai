# syntax=docker/dockerfile:1.7

ARG APP_HOME=/app
ARG RUNTIME_PACKAGES="curl ffmpeg tesseract-ocr tesseract-ocr-ita tesseract-ocr-eng libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1"
ARG BUILD_PACKAGES="build-essential"

########################
# Stage: build dependencies
########################
FROM python:3.11-slim as base

# Install additional packages
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ARG APP_HOME
ARG RUNTIME_PACKAGES
ARG BUILD_PACKAGES

ENV VENV_PATH=/opt/venv

WORKDIR ${APP_HOME}

# Create venv first (changes rarely)
RUN python -m venv ${VENV_PATH}
ENV PATH="${VENV_PATH}/bin:${PATH}"

# Install additional build packages
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    ${BUILD_PACKAGES} \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Python dependencies (only when requirements files change)
ARG REQUIREMENTS_FILE="requirements.txt"
COPY requirements*.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r ${REQUIREMENTS_FILE}

########################
# Stage: runtime base
########################
FROM base AS runtime-base

ARG APP_HOME
ARG RUNTIME_PACKAGES
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VENV_PATH=/opt/venv \
    PATH="${VENV_PATH}/bin:${PATH}"

WORKDIR ${APP_HOME}

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    ${RUNTIME_PACKAGES} \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY --from=base ${VENV_PATH} ${VENV_PATH}

########################
# Stage: development
########################
FROM runtime-base AS development

ARG APP_HOME

# Copia selettiva per migliore caching (in ordine dal meno al più frequente)
# 1. File di configurazione (cambiano raramente)
COPY main.py ./
COPY requirements*.py ./
COPY logging_config.py ./

# 2. Struttura directory applicative
COPY app/ ./app/
COPY services/ ./services/
COPY models/ ./models/
COPY utils/ ./utils/
COPY rag/ ./rag/
COPY middleware/ ./middleware/
COPY database/ ./database/

# 3. Inizializzazione directory dati
RUN mkdir -p data/courses data/vector_db data/uploads data/tracking && \
    chmod -R 755 data/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

########################
# Stage: production
########################
FROM runtime-base AS production

ARG APP_HOME

# Copia selettiva per production build (stesso ordine del development)
# 1. File di configurazione
COPY main.py ./
COPY requirements*.py ./
COPY logging_config.py ./
# Create backend directory structure to match import expectations
RUN mkdir -p backend
COPY logging_config.py ./backend/
# Create __init__.py to make backend a proper Python package
RUN echo "# Backend package" > ./backend/__init__.py

# 2. Codice applicativo
COPY app/ ./app/
COPY services/ ./services/
COPY models/ ./models/
COPY utils/ ./utils/
COPY rag/ ./rag/
COPY middleware/ ./middleware/
COPY database/ ./database/

# 3. Inizializzazione directory dati e configurazione security
RUN mkdir -p data/courses data/vector_db data/uploads data/tracking && \
    chmod -R 755 data/ && \
    adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser ${APP_HOME}

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
