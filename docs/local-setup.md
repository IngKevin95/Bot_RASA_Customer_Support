# Setup local — guía completa de desarrollo

Este documento explica cómo levantar todos los servicios del proyecto en tu máquina:
bot RASA, action server, backend FastAPI, frontend y Chatwoot (para demo de escalación).

---

## Prerequisitos

- Docker Desktop ≥ 24 (con Docker Compose v2)
- Python 3.10 (para desarrollo sin Docker del bot y el backend)
- Git

## Arquitectura de servicios

```
Browser → frontend:80 (nginx)
               └─→ proxy /api/* → backend:8000 (FastAPI)
                                      └─→ rasa:5005 (RASA Core + NLU)
                                                └─→ action-server:5055
                                      └─→ chatwoot:3000 (escalación demo)
                                                └─→ postgres:5432
                                                └─→ redis:6379
```

---

## Opción A: Stack completo con Docker Compose (recomendado)

```bash
# 1. Clonar y configurar variables de entorno
git clone https://github.com/IngKevin95/Bot_RASA_Customer_Support.git
cd Bot_RASA_Customer_Support
cp .env.example .env
cp .env.chatwoot.example .env.chatwoot

# 2. Editar .env:
#    - ESCALATION_PROVIDER=stub (por defecto, no requiere config adicional)
#    - Para demo con Chatwoot: ESCALATION_PROVIDER=chatwoot (ver sección Chatwoot abajo)

# 3. Entrenar el modelo RASA (necesario antes del primer docker compose up)
pip install rasa==3.6.21
make train   # o: rasa train --fixed-model-name latest

# 4. Levantar todos los servicios
make all-up  # o: docker compose up --build

# Servicios disponibles:
#   Frontend:    http://localhost
#   Backend API: http://localhost:8000/docs  (Swagger UI)
#   RASA:        http://localhost:5005
#   Chatwoot:    http://localhost:3000
```

---

## Opción B: Servicios individuales en desarrollo

Más útil para desarrollo cuando se quiere hot-reload en el backend o el bot.

```bash
# Terminal 1 — Action server
pip install -r requirements-dev.txt
make actions       # rasa run actions --port 5055

# Terminal 2 — RASA (requiere modelo entrenado)
make train         # entrenar el modelo (hacerlo al menos una vez)
make run           # rasa run --enable-api --cors "*" --port 5005

# Terminal 3 — Backend FastAPI
make backend-install   # instala requirements del backend
make backend           # uvicorn app.main:app --reload --port 8000

# Terminal 4 — Frontend (sin Docker)
make frontend-serve    # python -m http.server 8080 -d frontend
# Abrir: http://localhost:8080
# NOTA: en modo local el JS necesita apuntar a http://localhost:8000/api/v1
#       cambiar la linea API_BASE al inicio de frontend/js/chat.js
```

---

## Configuración de Chatwoot (demo de escalación)

Para ver la escalación real creando conversaciones en Chatwoot:

```bash
# 1. Asegurarse de que Chatwoot esté corriendo
docker compose up chatwoot postgres redis -d

# 2. Entrar a http://localhost:3000 y crear cuenta de administrador

# 3. Crear un Inbox de tipo API en Settings > Inboxes > Add Inbox > API

# 4. Copiar el API Access Token de Settings > Profile > Access Token

# 5. Completar en .env:
ESCALATION_PROVIDER=chatwoot
CHATWOOT_URL=http://localhost:3000
CHATWOOT_API_TOKEN=<tu_token>
CHATWOOT_ACCOUNT_ID=1
CHATWOOT_INBOX_ID=<id_del_inbox_creado>

# 6. Reiniciar el stack
docker compose up --build -d
```

Cuando un usuario escriba "necesito un agente" en el chat, el backend creará
automáticamente una conversación en Chatwoot que aparece en el panel de agentes.

---

## Configuración de Genesys Cloud

Genesys Cloud es SaaS y **no se puede desplegar localmente**. Para probarlo
se necesita una organización activa en Genesys Cloud (ver [gcp-setup.md](gcp-setup.md)
para contexto de producción).

```bash
# En .env:
ESCALATION_PROVIDER=genesys
GENESYS_CLIENT_ID=<client_id_de_tu_org>
GENESYS_CLIENT_SECRET=<client_secret>
GENESYS_ORG_ID=mypurecloud.com   # o tu region: mypurecloud.ie, usw2.pure.cloud, etc.
```

Sin `conversation_id` y `participant_id` activos (que vienen del canal WebChat de Genesys),
el provider hace una respuesta de demo sin error — así el flujo del bot no se rompe en desarrollo.

---

## Tests

```bash
# Tests del bot RASA (unit tests de actions)
pytest tests/ -v --cov=actions --cov-report=term-missing

# Tests del backend FastAPI
cd backend && pytest tests/ -v
```

---

## Troubleshooting

| Problema | Solución |
|----------|----------|
| Puerto 5005 ocupado | `lsof -i :5005` y matar el proceso, o cambiar el puerto en `.env` |
| "Model not found" en RASA | Correr `make train` primero, esperar ~3 minutos |
| Chatwoot no inicia | Verificar que postgres y redis estén corriendo: `docker compose ps` |
| CORS error en browser | Usar el stack completo con nginx (`make all-up`) en lugar de servir el frontend directo |
| Backend no conecta a RASA | RASA tarda ~60s en arrancar — el health check en `/api/v1/health` muestra el estado |

---

## Makefile targets disponibles

```bash
make help           # ver todos los targets
make train          # entrenar modelo RASA
make test           # unit tests del bot
make test-cov       # tests con cobertura
make actions        # iniciar action server (:5055)
make run            # iniciar RASA (:5005)
make backend        # iniciar backend FastAPI (:8000)
make backend-install # instalar dependencias del backend
make frontend-serve # servir frontend en :8080 (sin Docker)
make all-up         # docker compose up --build (stack completo)
make all-down       # docker compose down -v
make lint           # validar datos de entrenamiento RASA
```
