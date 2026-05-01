# SKILL.md — Contexto para Agentes de IA

## Descripción del Proyecto

Sistema de procesamiento asíncrono de reportes para una plataforma SaaS de analítica. Arquitectura productor-consumidor donde un API REST (FastAPI) publica trabajos en AWS SQS y workers concurrentes los procesan en segundo plano, con persistencia en DynamoDB y un frontend React.

## Estructura del Proyecto

```
├── backend/                    # API REST — FastAPI (Python 3.11)
│   ├── app/
│   │   ├── main.py            # Entry point, registra routers y exception handlers
│   │   ├── config.py          # Pydantic Settings (variables de entorno)
│   │   ├── dependencies.py    # Inyección de dependencias (DB, SQS clients)
│   │   ├── auth/
│   │   │   ├── router.py      # POST /auth/register, POST /auth/login
│   │   │   ├── service.py     # Hash bcrypt, generación/verificación JWT
│   │   │   ├── schemas.py     # LoginRequest, RegisterRequest, TokenResponse
│   │   │   └── middleware.py  # Dependencia FastAPI para extraer user_id del JWT
│   │   ├── jobs/
│   │   │   ├── router.py      # POST /jobs, GET /jobs, GET /jobs/{job_id}
│   │   │   ├── service.py     # Lógica de negocio: crear, consultar, listar
│   │   │   ├── schemas.py     # JobCreateRequest, JobResponse, JobListResponse
│   │   │   └── enums.py       # JobStatus: PENDING, PROCESSING, COMPLETED, FAILED
│   │   ├── stream/
│   │   │   ├── router.py      # GET /stream/jobs (SSE)
│   │   │   └── service.py     # Polling DynamoDB + emisión SSE
│   │   ├── db/
│   │   │   ├── client.py      # Cliente boto3 DynamoDB (configurable endpoint)
│   │   │   ├── repository.py  # CRUD jobs: create, get, update_status, list_by_user
│   │   │   └── user_repository.py  # CRUD users: create, get_by_username
│   │   ├── queue/
│   │   │   ├── client.py      # Cliente boto3 SQS (configurable endpoint)
│   │   │   └── publisher.py   # publish_job_message (estándar o alta prioridad)
│   │   ├── observability/
│   │   │   ├── logging.py     # Logging JSON estructurado
│   │   │   └── metrics.py     # Métricas en memoria
│   │   └── errors/
│   │       └── handlers.py    # Exception handlers globales (422, 401, 403, 404, 500)
│   ├── tests/
│   │   ├── unit/              # Tests unitarios
│   │   ├── integration/       # Tests de integración
│   │   ├── property/          # Tests basados en propiedades (hypothesis)
│   │   └── conftest.py        # Fixtures: moto mocks, test client, auth headers
│   ├── Dockerfile             # Multi-stage, Python slim, usuario no-root
│   └── requirements.txt
│
├── worker/                    # Consumidor SQS + procesador (Python 3.11)
│   ├── app/
│   │   ├── main.py           # Entry point: inicia loop asyncio
│   │   ├── config.py         # Pydantic Settings del worker
│   │   ├── consumer.py       # Polling SQS, procesamiento paralelo (asyncio)
│   │   ├── processor.py      # Generación simulada de reportes (sleep 5-30s)
│   │   ├── circuit_breaker.py # Patrón Circuit Breaker (bonus)
│   │   ├── retry.py          # Backoff exponencial con jitter (bonus)
│   │   ├── db/
│   │   │   ├── client.py     # Cliente DynamoDB del worker
│   │   │   └── repository.py # update_job_status, get_job
│   │   └── observability/
│   │       └── logging.py    # Logging JSON estructurado
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                  # React 18 + Vite + TypeScript
│   ├── src/
│   │   ├── App.tsx           # Routing: LoginPage ↔ DashboardPage
│   │   ├── main.tsx          # Entry point React
│   │   ├── api/
│   │   │   └── client.ts    # HTTP client con JWT automático en headers
│   │   ├── hooks/
│   │   │   ├── useAuth.ts   # Login, registro, almacenamiento token
│   │   │   ├── useJobs.ts   # CRUD trabajos + polling cada 5s
│   │   │   └── useSSE.ts    # EventSource con fallback a polling
│   │   ├── components/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── JobForm.tsx       # report_type, date_range, format
│   │   │   ├── JobList.tsx       # Lista con badges de estado
│   │   │   ├── JobStatusBadge.tsx # Colores: yellow/blue/green/red
│   │   │   ├── Toast.tsx         # Notificaciones (sin alert() nativo)
│   │   │   └── Layout.tsx        # Responsive (320px - 1024px+)
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   └── DashboardPage.tsx
│   │   └── types/
│   │       └── index.ts     # Job, JobCreatePayload, TokenResponse, etc.
│   ├── Dockerfile            # Multi-stage: Node build → Nginx serve
│   ├── nginx.conf
│   └── package.json
│
├── infra/
│   ├── terraform/            # IaC producción
│   │   ├── main.tf          # Provider AWS
│   │   ├── variables.tf     # Configuración parametrizada
│   │   ├── outputs.tf       # URLs y ARNs
│   │   ├── dynamodb.tf      # Tablas jobs + users con GSIs
│   │   ├── sqs.tf           # 4 colas (estándar, high, 2 DLQs)
│   │   ├── compute.tf       # EC2 t2.micro + VPC + Security Group
│   │   └── iam.tf           # Roles con permisos DynamoDB + SQS
│   └── localstack/
│       └── init-aws.sh      # Crea tablas y colas en LocalStack
│
├── .github/workflows/
│   └── deploy.yml           # CI/CD: test → build → deploy via SSH
│
├── docker-compose.yml        # Orquestación local completa
├── .env.example              # Variables de entorno documentadas
├── README.md                 # Instrucciones de setup y uso
├── TECHNICAL_DOCS.md         # Arquitectura y decisiones de diseño
└── AI_WORKFLOW.md            # Evidencia de uso de herramientas IA
```

## Convenciones del Código

### Backend (Python)

- **Framework:** FastAPI con async/await
- **Validación:** Pydantic v2 BaseModel para todos los request/response
- **Configuración:** Pydantic Settings (carga de variables de entorno)
- **Estructura:** Router → Service → Repository (capas separadas)
- **Autenticación:** JWT con PyJWT, bcrypt para hashing de contraseñas
- **AWS SDK:** boto3 con endpoint configurable (LocalStack en dev, AWS real en prod)
- **Errores:** Exception handlers globales, modelo ErrorResponse uniforme
- **Logging:** JSON estructurado con campos: timestamp, level, message, request_id
- **Testing:** pytest + hypothesis (property-based) + moto (AWS mocks)

### Worker (Python)

- **Concurrencia:** asyncio con semáforo para limitar paralelismo
- **Polling:** Long polling de SQS con intervalo configurable
- **Resiliencia:** Circuit Breaker (5 fallos → open 60s) + Backoff exponencial (1s, 2s, 4s ± 500ms jitter)
- **Estado:** Actualiza DynamoDB en cada transición (PENDING → PROCESSING → COMPLETED/FAILED)

### Frontend (TypeScript/React)

- **Build:** Vite con TypeScript estricto
- **Estado:** Hooks personalizados (useAuth, useJobs, useSSE)
- **HTTP:** Fetch API con interceptor JWT automático
- **Actualizaciones:** Polling cada 5s con fallback desde SSE
- **UI:** Responsive (320px+), sin alert() nativo, badges de color por estado
- **Notificaciones:** Componente Toast para errores y confirmaciones

## Patrones Clave

### Flujo de Creación de Trabajo
1. Frontend envía POST /jobs con JWT
2. API valida con Pydantic, crea registro PENDING en DynamoDB
3. API publica mensaje en SQS (cola según prioridad)
4. Si SQS falla → marca FAILED, retorna 503
5. Retorna 201 con job_id

### Flujo de Procesamiento
1. Worker hace long polling a SQS (prioridad alta primero)
2. Recibe mensaje → actualiza estado a PROCESSING
3. Genera reporte (simulado con sleep aleatorio)
4. Éxito → COMPLETED + result_url; Fallo → reintentos con backoff → FAILED
5. Elimina mensaje de SQS tras éxito

### Autenticación
- POST /auth/register → crea usuario con password hasheado (bcrypt)
- POST /auth/login → verifica credenciales, retorna JWT (HS256, exp configurable)
- Endpoints protegidos → middleware extrae user_id del token
- Token expirado/inválido/ausente → 401

### Aislamiento de Datos
- Cada usuario solo ve sus propios trabajos
- GET /jobs filtra por user_id del JWT
- GET /jobs/{job_id} verifica que user_id del trabajo == user_id del token → 403 si no coincide

## Dependencias Principales

### Backend
- `fastapi==0.115.0` — Framework web async
- `uvicorn==0.30.6` — Servidor ASGI
- `pydantic==2.9.2` — Validación de datos
- `pydantic-settings==2.5.2` — Configuración desde env vars
- `pyjwt==2.9.0` — Tokens JWT
- `bcrypt==4.2.0` — Hashing de contraseñas
- `boto3==1.35.19` — AWS SDK (DynamoDB, SQS)

### Worker
- `boto3>=1.34.0` — AWS SDK
- `pydantic>=2.5.0` — Validación de mensajes
- `pydantic-settings>=2.1.0` — Configuración

### Frontend
- `react@^18.2.0` — UI library
- `react-dom@^18.2.0` — DOM rendering
- `vite@^4.4.5` — Build tool
- `typescript@^5.0.2` — Type safety

## Servicios AWS

| Servicio | Recurso | Propósito |
|----------|---------|-----------|
| DynamoDB | Tabla `jobs` | Persistencia de trabajos (PK: job_id, GSI: user_id+created_at) |
| DynamoDB | Tabla `users` | Persistencia de usuarios (PK: user_id, GSI: username) |
| SQS | `reports-queue-standard` | Cola principal de trabajos |
| SQS | `reports-queue-high` | Cola de alta prioridad |
| SQS | `reports-dlq-standard` | Dead letter queue (3 reintentos) |
| SQS | `reports-dlq-high` | Dead letter queue alta prioridad |
| EC2 | t2.micro | Instancia de producción (Docker Compose) |

## Comandos Útiles

```bash
# Desarrollo local completo
docker compose up

# Solo backend en modo desarrollo
cd backend && uvicorn app.main:app --reload

# Tests backend
cd backend && pytest tests/ -v

# Tests con cobertura
cd backend && pytest tests/ --cov=app --cov-report=term-missing

# Frontend dev
cd frontend && npm run dev

# Terraform plan
cd infra/terraform && terraform plan
```

## Variables de Entorno Críticas

| Variable | Descripción | Notas |
|----------|-------------|-------|
| `AWS_ENDPOINT_URL` | Solo para dev (LocalStack) | Omitir en producción |
| `JWT_SECRET` | Secreto de firma JWT | DEBE cambiarse en producción |
| `WORKER_CONCURRENCY` | Mensajes paralelos | Default: 2 |
| `SQS_STANDARD_QUEUE_URL` | URL cola principal | Diferente en dev vs prod |
| `SQS_HIGH_QUEUE_URL` | URL cola prioridad | Diferente en dev vs prod |

## Notas para Agentes de IA

- El proyecto usa **LocalStack** para desarrollo local — todas las llamadas a AWS van a `http://localstack:4566` en Docker
- La generación de reportes es **simulada** (sleep aleatorio) — no hay lógica real de generación de datos
- El frontend usa **polling cada 5 segundos** como mecanismo principal de actualización, con SSE como mejora opcional
- Los tests usan **moto** para mockear AWS — no requieren LocalStack ni conexión real a AWS
- La autenticación es **stateless** — no hay tabla de sesiones, todo está en el JWT
- El worker procesa **mínimo 2 mensajes en paralelo** usando asyncio
- Los errores del API siempre retornan el modelo `ErrorResponse` con campos `detail` y `field` opcional
