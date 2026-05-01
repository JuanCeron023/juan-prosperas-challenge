# Sistema de Procesamiento Asíncrono de Reportes

[![Deploy to AWS](https://github.com/<OWNER>/<REPO>/actions/workflows/deploy.yml/badge.svg)](https://github.com/<OWNER>/<REPO>/actions/workflows/deploy.yml)

Sistema completo de procesamiento asíncrono de reportes para una plataforma SaaS de analítica. Los usuarios solicitan reportes bajo demanda que se procesan en segundo plano mediante una arquitectura basada en colas de mensajes (AWS SQS) y workers concurrentes, con persistencia en AWS DynamoDB.

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Frontend   │────▶│  Backend API │────▶│   AWS SQS   │
│  (React 18) │     │  (FastAPI)   │     │  (Cola)     │
└─────────────┘     └──────┬───────┘     └──────┬──────┘
                           │                     │
                           ▼                     ▼
                    ┌──────────────┐     ┌─────────────┐
                    │  DynamoDB    │◀────│   Worker    │
                    │  (Estado)    │     │  (asyncio)  │
                    └──────────────┘     └─────────────┘
```

## Requisitos Previos

- Docker y Docker Compose v2+
- Git
- (Opcional) Python 3.11+ para desarrollo sin Docker
- (Opcional) Node.js 18+ para desarrollo del frontend sin Docker

## Inicio Rápido — Desarrollo Local

1. **Clonar el repositorio:**
   ```bash
   git clone <REPO_URL>
   cd async-report-processing
   ```

2. **Configurar variables de entorno:**
   ```bash
   cp .env.example .env
   ```

3. **Levantar todos los servicios:**
   ```bash
   docker compose up
   ```

   Esto levanta automáticamente:
   - **LocalStack** (emulador AWS) — puerto 4566
   - **Backend API** (FastAPI) — http://localhost:8000
   - **Worker** (consumidor SQS)
   - **Frontend** (React + Nginx) — http://localhost:3000

4. **Verificar que todo funciona:**
   ```bash
   # Health check del API
   curl http://localhost:8000/health

   # Documentación OpenAPI
   open http://localhost:8000/docs
   ```

## Comandos de Desarrollo

### Docker Compose (recomendado)

```bash
# Levantar todos los servicios
docker compose up

# Levantar en background
docker compose up -d

# Reconstruir imágenes tras cambios
docker compose up --build

# Ver logs de un servicio específico
docker compose logs -f backend
docker compose logs -f worker

# Detener todos los servicios
docker compose down

# Detener y eliminar volúmenes
docker compose down -v
```

### Backend (desarrollo sin Docker)

```bash
cd backend

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor de desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Ejecutar tests
pip install pytest pytest-asyncio moto[all] httpx hypothesis
pytest tests/ -v
```

### Worker (desarrollo sin Docker)

```bash
cd worker

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar worker
python -m app.main
```

### Frontend (desarrollo sin Docker)

```bash
cd frontend

# Instalar dependencias
npm install

# Servidor de desarrollo con hot reload
npm run dev

# Build de producción
npm run build

# Lint
npm run lint
```

### Infraestructura (Terraform)

```bash
cd infra/terraform

# Inicializar Terraform
terraform init

# Ver plan de cambios
terraform plan

# Aplicar infraestructura
terraform apply

# Destruir infraestructura
terraform destroy
```

## Variables de Entorno

Ver `.env.example` para la lista completa de variables con descripciones.

| Variable | Descripción | Default (dev) |
|----------|-------------|---------------|
| `AWS_REGION` | Región AWS | `us-east-1` |
| `AWS_ENDPOINT_URL` | Endpoint LocalStack (solo dev) | `http://localhost:4566` |
| `JWT_SECRET` | Secreto para firmar tokens JWT | `change-me-in-production` |
| `JWT_EXPIRATION_MINUTES` | Expiración del token en minutos | `60` |
| `DYNAMODB_JOBS_TABLE` | Nombre de la tabla de trabajos | `jobs` |
| `DYNAMODB_USERS_TABLE` | Nombre de la tabla de usuarios | `users` |
| `SQS_STANDARD_QUEUE_URL` | URL de la cola estándar | (ver .env.example) |
| `SQS_HIGH_QUEUE_URL` | URL de la cola de alta prioridad | (ver .env.example) |
| `WORKER_CONCURRENCY` | Mensajes procesados en paralelo | `2` |

## URL de Producción

> **Placeholder:** La URL de producción se genera tras el despliegue con Terraform y se registra en los logs del pipeline CI/CD.
>
> ```
> http://<EC2_PUBLIC_IP>
> ```

## Estructura del Proyecto

```
├── backend/              # API REST (FastAPI + Python 3.11)
├── worker/               # Consumidor SQS + procesador de reportes
├── frontend/             # Interfaz web (React 18 + Vite + TypeScript)
├── infra/
│   ├── terraform/        # IaC para producción (AWS)
│   └── localstack/       # Scripts de inicialización local
├── .github/workflows/    # Pipeline CI/CD
├── docker-compose.yml    # Orquestación local
├── .env.example          # Variables de entorno documentadas
├── TECHNICAL_DOCS.md     # Documentación técnica detallada
├── SKILL.md              # Contexto para agentes de IA
└── AI_WORKFLOW.md        # Evidencia de uso de herramientas IA
```

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/auth/register` | Registro de usuario | No |
| POST | `/auth/login` | Login, retorna JWT | No |
| POST | `/jobs` | Crear trabajo de reporte | JWT |
| GET | `/jobs` | Listar trabajos paginados | JWT |
| GET | `/jobs/{job_id}` | Consultar estado de trabajo | JWT |
| GET | `/health` | Health check del sistema | No |
| GET | `/stream/jobs` | Stream SSE (bonus) | JWT |

## Licencia

MIT
