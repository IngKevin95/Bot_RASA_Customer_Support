# Setup GCP para deploy automatico

Este documento describe los pasos necesarios para que el workflow `.github/workflows/deploy.yml` funcione correctamente. El workflow falla si los secrets `GCP_PROJECT_ID` y `GCP_SA_KEY` no estan configurados en el repositorio.

---

## Resumen de lo que necesitas

| Recurso | Descripcion |
|---|---|
| Proyecto GCP | Con facturacion habilitada |
| APIs habilitadas | Cloud Run, Cloud Build, Container Registry |
| Service Account | Con los roles necesarios para deploy |
| Clave JSON del SA | Descargada y guardada como secret en GitHub |

---

## Paso 1 — Crear o seleccionar un proyecto GCP

```bash
# Crear proyecto nuevo
gcloud projects create mi-bot-soporte --name="Customer Support Bot"

# O listar proyectos existentes y seleccionar uno
gcloud projects list
gcloud config set project TU-PROJECT-ID
```

Asegurate de tener facturacion habilitada:
- Console GCP → Billing → Link a billing account al proyecto

---

## Paso 2 — Habilitar las APIs necesarias

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  iam.googleapis.com
```

Esto puede tardar 1-2 minutos. Verificar con:

```bash
gcloud services list --enabled --filter="name:(run OR cloudbuild OR containerregistry)"
```

---

## Paso 3 — Crear el Service Account

```bash
gcloud iam service-accounts create github-actions-sa \
  --display-name="GitHub Actions - Customer Support Bot" \
  --description="SA para deploy automatico desde GitHub Actions"
```

Verificar que se creo:

```bash
gcloud iam service-accounts list --filter="email:github-actions-sa"
```

---

## Paso 4 — Asignar roles al Service Account

El SA necesita permisos para: subir imagenes a Container Registry, hacer deploy en Cloud Run, y actuar como service account.

```bash
PROJECT_ID=$(gcloud config get-value project)
SA_EMAIL="github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Permisos de Cloud Run
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.admin"

# Permisos de Container Registry (subir imagenes Docker)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin"

# Permisos para actuar como SA en deploys
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"

# Permisos de Cloud Build (para gcloud builds submit si se usa)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudbuild.builds.editor"
```

Verificar los roles asignados:

```bash
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:github-actions-sa"
```

---

## Paso 5 — Generar y descargar la clave JSON

```bash
PROJECT_ID=$(gcloud config get-value project)
SA_EMAIL="github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts keys create gcp-key.json \
  --iam-account=$SA_EMAIL
```

Esto genera el archivo `gcp-key.json` en el directorio actual. **No subir este archivo al repositorio** — ya esta en `.gitignore` (todos los `.json` con "key" en el nombre deben estar ignorados).

Verificar el contenido del JSON — debe tener esta estructura:

```json
{
  "type": "service_account",
  "project_id": "tu-proyecto",
  "private_key_id": "...",
  "private_key": "-----BEGIN RSA PRIVATE KEY-----...",
  "client_email": "github-actions-sa@tu-proyecto.iam.gserviceaccount.com",
  ...
}
```

---

## Paso 6 — Configurar los secrets en GitHub

En el repositorio de GitHub:

1. Ir a **Settings → Secrets and variables → Actions**
2. Hacer click en **New repository secret**

**Secret 1: `GCP_PROJECT_ID`**
- Name: `GCP_PROJECT_ID`
- Value: el ID del proyecto (ej: `mi-bot-soporte-123456`)

**Secret 2: `GCP_SA_KEY`**
- Name: `GCP_SA_KEY`
- Value: el contenido completo del archivo `gcp-key.json` (copiar y pegar el JSON entero)

Una vez guardados, **eliminar el archivo** `gcp-key.json` del disco:

```bash
rm gcp-key.json
```

---

## Paso 7 — Verificar el workflow

Hacer un push a `main` (o mergear un PR) y revisar la tab **Actions** en GitHub. El job `Build & Deploy` debe pasar por estos pasos:

1. Checkout del codigo
2. Autenticacion con GCP (este es el que falla sin los secrets)
3. Setup de Cloud SDK
4. Entrenamiento del modelo RASA
5. Build de la imagen Docker
6. Push a Container Registry
7. Deploy en Cloud Run
8. Log de la URL del servicio

Si el deploy es exitoso, Cloud Run genera una URL publica del tipo:
`https://customer-support-bot-HASH-uc.a.run.app`

---

## Alternativa mas segura: Workload Identity Federation

La opcion con clave JSON funciona pero tiene una desventaja: la clave es un secreto de larga duracion que hay que rotar periodicamente. Para produccion real, la alternativa recomendada por Google es **Workload Identity Federation**, que permite a GitHub Actions autenticarse en GCP sin necesidad de claves JSON.

La configuracion es mas compleja pero vale la pena si el proyecto va a vivir en produccion de verdad. La documentacion oficial esta en:
https://github.com/google-github-actions/auth?tab=readme-ov-file#workload-identity-federation-through-a-service-account

El workflow solo cambiaria el step de autenticacion:

```yaml
- name: Authenticate to GCP
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER
    service_account: github-actions-sa@PROJECT_ID.iam.gserviceaccount.com
```

Sin necesidad de `GCP_SA_KEY`.

---

## Estimacion de costos GCP

Para un bot de soporte con carga baja/media en Cloud Run:

| Recurso | Costo estimado |
|---|---|
| Cloud Run (0.5M requests/mes) | ~$0 (incluido en free tier) |
| Container Registry (imagen ~2GB) | ~$0.05/mes |
| Cloud Build (si se usa) | ~$0 (120 min/dia gratis) |
| **Total estimado** | **< $1/mes** con trafico bajo |

Cloud Run escala a cero cuando no hay trafico, por lo que no hay costo en horas sin uso.
