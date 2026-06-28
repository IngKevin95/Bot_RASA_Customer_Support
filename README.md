# Customer Support Bot — RASA + GCP Cloud Run

Bot conversacional de soporte al cliente con NLP/NLU usando RASA, deployado en Google Cloud Platform.

---

## Arquitectura

```
Cliente HTTP (Postman / Frontend / Genesys)
        │
        │  POST /webhooks/rest/webhook
        ▼
┌─────────────────────────────────────┐
│         RASA Server (port 8080)      │
│  - NLU: clasifica intents            │
│  - Core: maneja flujos de dialogo    │
│  - REST API habilitada               │
└──────────────┬──────────────────────┘
               │ HTTP (action calls)
               ▼
┌─────────────────────────────────────┐
│       Action Server (port 5055)      │
│  - action_check_balance              │
│  - action_process_payment            │
│  - action_escalate_agent             │
└─────────────────────────────────────┘

Deploy: GCP Cloud Run (Docker, serverless, auto-scaling)
CI/CD:  GitHub Actions → Cloud Build → Cloud Run
```

---

## Intents y entidades

| Intent | Descripcion | Ejemplo |
|---|---|---|
| `greet` | Saludo | "hola", "buenos dias" |
| `goodbye` | Despedida | "adios", "hasta luego" |
| `check_balance` | Consultar saldo | "cual es mi saldo?" |
| `make_payment` | Realizar pago | "quiero pagar 500 a la cuenta 1234" |
| `request_help` | Solicitar ayuda | "necesito ayuda" |

| Entidad | Descripcion | Ejemplo |
|---|---|---|
| `account_number` | Numero de cuenta | "1234567" |
| `amount` | Monto a pagar | "500", "1000" |

---

## Setup local

### 1. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Entrenar el modelo

```bash
rasa train
```

El modelo se guarda en `models/`. El entrenamiento tarda ~2-5 minutos.

### 4. Iniciar el bot

```bash
# Terminal 1: action server
rasa run actions

# Terminal 2: rasa con API REST habilitada
rasa run --enable-api --cors "*" --port 5005 --endpoints endpoints.yml
```

### 5. Probar

```bash
# Saludo
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "user1", "message": "hola"}'

# Consultar saldo
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "user1", "message": "cual es mi saldo de la cuenta 1234567"}'

# Hacer un pago
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "user1", "message": "quiero pagar 500 en la cuenta 9876543"}'
```

### Alternativa: shell interactivo

```bash
rasa shell
```

---

## Docker (local)

```bash
# Construir y levantar todo
docker compose up --build

# El bot queda disponible en http://localhost:5005
```

---

## Deploy en GCP Cloud Run

### Pre-requisitos

- Cuenta GCP con Cloud Run y Cloud Build habilitados
- `gcloud` CLI instalado y autenticado
- Docker instalado

### Manual

```bash
# 1. Entrenar modelo primero
rasa train --fixed-model-name latest

# 2. Configurar proyecto GCP
gcloud config set project TU-PROJECT-ID

# 3. Build y push imagen
gcloud builds submit --tag gcr.io/TU-PROJECT-ID/customer-support-bot

# 4. Deploy
gcloud run deploy customer-support-bot \
  --image gcr.io/TU-PROJECT-ID/customer-support-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi
```

### CI/CD automatico (GitHub Actions)

Agrega estos secrets en tu repo de GitHub (`Settings > Secrets`):

| Secret | Valor |
|---|---|
| `GCP_PROJECT_ID` | ID de tu proyecto GCP |
| `GCP_SA_KEY` | JSON de tu service account con permisos Cloud Run + Cloud Build |

Cada push a `main` dispara el deploy automaticamente.

---

## Ejecutar tests

```bash
rasa test
```

Evalua NLU accuracy y flujos de conversacion contra `tests/test_stories.yml`.

---

## Variables de entorno

Copia `.env.example` a `.env` y completa los valores:

```bash
cp .env.example .env
```

> `.env` esta en `.gitignore` — nunca lo subas al repositorio.

---

## Estructura del proyecto

```
customer-support-bot/
├── .github/workflows/deploy.yml   # CI/CD a GCP
├── actions/
│   └── actions.py                 # Logica de negocio (saldo, pagos, escalado)
├── data/
│   ├── nlu.yml                    # Training data (intents + entities)
│   ├── stories.yml                # Flujos de conversacion
│   └── rules.yml                  # Reglas deterministas
├── tests/
│   └── test_stories.yml           # Tests end-to-end
├── config.yml                     # Pipeline NLU/NLG
├── domain.yml                     # Intents, slots, responses, actions
├── endpoints.yml                  # Conexion action server
├── Dockerfile                     # Multi-stage build
├── docker-compose.yml             # Dev local
├── requirements.txt
└── .env.example
```

---

## Integracion con Genesys Cloud

El endpoint `/webhooks/rest/webhook` es compatible con Genesys Cloud Architect:

```
Genesys Cloud → Call Data Action → POST /webhooks/rest/webhook
Body: { "sender": "{ConversationId}", "message": "{CustomerInput}" }
```

La accion `action_escalate_agent` puede extenderse con el SDK de Genesys para transferir la sesion a una cola real.

---

## Tecnologias

- **RASA 3.6** — NLP/NLU + dialogue management
- **Python 3.10** — runtime
- **Docker** — containerizacion
- **GCP Cloud Run** — serverless deployment
- **GitHub Actions** — CI/CD
