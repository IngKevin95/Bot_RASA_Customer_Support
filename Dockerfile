# --- Stage 1: builder ---
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# --- Stage 2: runtime ---
FROM python:3.10-slim

WORKDIR /app

# Copiar dependencias del builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copiar proyecto
COPY . .

# Cloud Run requiere puerto 8080
ENV PORT=8080

# Exponer action server y rasa
EXPOSE 5055 8080

# Entrypoint: iniciar action server + rasa en paralelo
CMD rasa run actions --port 5055 & \
    rasa run \
      --enable-api \
      --cors "*" \
      --port ${PORT} \
      --endpoints endpoints.yml \
      --credentials credentials.yml
