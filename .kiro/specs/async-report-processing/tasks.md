# Plan de Implementación: Sistema de Procesamiento Asíncrono de Reportes

## Resumen

Plan de implementación incremental para el sistema de procesamiento asíncrono de reportes. Cada tarea construye sobre las anteriores, comenzando por la estructura del proyecto y modelos de datos, pasando por la lógica de negocio core, hasta la integración completa con infraestructura, frontend y CI/CD. Las tareas bonus (B1-B6) están marcadas como opcionales.

## Tareas

- [x] 1. Estructura del proyecto y configuración base
  - [x] 1.1 Crear estructura de directorios del backend y configuración
    - Crear la estructura `backend/app/` con los módulos: `auth/`, `jobs/`, `stream/`, `db/`, `queue/`, `observability/`, `errors/`
    - Crear `backend/requirements.txt` con dependencias: fastapi, uvicorn, pydantic[settings], pyjwt, bcrypt, boto3, python-multipart
    - Crear `backend/app/config.py` con Pydantic Settings para variables de entorno (AWS endpoints, JWT_SECRET, tabla DynamoDB, colas SQS, etc.)
    - Crear `backend/app/jobs/enums.py` con el enum `JobStatus` (PENDING, PROCESSING, COMPLETED, FAILED)
    - _Requisitos: 5.1, 8.1_

  - [x] 1.2 Crear estructura de directorios del worker y configuración
    - Crear la estructura `worker/app/` con los módulos: `db/`, `observability/`
    - Crear `worker/requirements.txt` con dependencias: boto3, pydantic, pydantic-settings
    - Crear `worker/app/config.py` con Pydantic Settings para variables de entorno del worker
    - _Requisitos: 7.1_

  - [x] 1.3 Crear estructura de directorios del frontend
    - Inicializar proyecto React 18+ con Vite y TypeScript
    - Crear la estructura `frontend/src/` con los directorios: `api/`, `hooks/`, `components/`, `pages/`, `types/`
    - Crear `frontend/src/types/index.ts` con las interfaces TypeScript: `Job`, `JobCreatePayload`, `JobListResponse`, `TokenResponse`, `ErrorResponse`
    - Definir constante `STATUS_COLORS` con los colores por estado (PENDING→yellow, PROCESSING→blue, COMPLETED→green, FAILED→red)
    - _Requisitos: 9.1, 9.4_

- [x] 2. Modelos de datos y capa de persistencia (DynamoDB)
  - [x] 2.1 Implementar cliente DynamoDB y repositorio de trabajos
    - Crear `backend/app/db/client.py` con la inicialización del cliente boto3 DynamoDB (configurable para LocalStack o AWS real)
    - Crear `backend/app/db/repository.py` con las operaciones CRUD: `create_job`, `get_job`, `update_job_status`, `list_jobs_by_user` (paginado con cursor usando GSI `user-jobs-index`)
    - Implementar actualización automática de `updated_at` en cada modificación
    - _Requisitos: 1.4, 8.1, 8.2, 8.3, 3.1, 3.2, 3.3, 3.4_

  - [ ]* 2.2 Escribir test de propiedad para persistencia round trip
    - **Propiedad 4: Persistencia completa en DynamoDB (round trip)**
    - **Valida: Requisitos 1.4, 8.1**

  - [x] 2.3 Implementar repositorio de usuarios
    - Crear tabla `users` con campos: user_id (PK), username, password_hash, created_at
    - Implementar operaciones: `create_user`, `get_user_by_username` (usando GSI `username-index`)
    - _Requisitos: 4.6_

- [x] 3. Autenticación JWT
  - [x] 3.1 Implementar servicio de autenticación
    - Crear `backend/app/auth/service.py` con lógica de hash de contraseñas (bcrypt), generación de JWT (PyJWT con HS256) y verificación de tokens
    - Implementar funciones: `hash_password`, `verify_password`, `create_access_token`, `decode_token`
    - Token JWT debe contener: sub (user_id), username, exp, iat
    - _Requisitos: 4.1, 4.5_

  - [x] 3.2 Implementar schemas Pydantic de autenticación
    - Crear `backend/app/auth/schemas.py` con modelos: `LoginRequest`, `RegisterRequest` (username min 3, password min 8), `TokenResponse`
    - _Requisitos: 4.1, 4.6, 5.1_

  - [x] 3.3 Implementar middleware JWT y router de autenticación
    - Crear `backend/app/auth/middleware.py` con dependencia FastAPI que extraiga y valide el token JWT del header Authorization
    - Crear `backend/app/auth/router.py` con endpoints POST `/auth/register` (201) y POST `/auth/login` (200 con token)
    - Manejar credenciales inválidas (401), token ausente/expirado/inválido (401)
    - _Requisitos: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 3.4 Escribir tests de propiedad para autenticación
    - **Propiedad 9: Login válido retorna JWT firmado**
    - **Propiedad 10: Autenticación rechaza tokens inválidos**
    - **Propiedad 11: Extracción de user_id del JWT (round trip)**
    - **Valida: Requisitos 4.1, 4.2, 4.3, 4.4, 4.5**

- [x] 4. Cola de mensajes SQS y publicación
  - [x] 4.1 Implementar cliente SQS y publicador de mensajes
    - Crear `backend/app/queue/client.py` con inicialización del cliente boto3 SQS (configurable para LocalStack o AWS real)
    - Crear `backend/app/queue/publisher.py` con función `publish_job_message` que publique el mensaje JSON con campos: job_id, user_id, report_type, date_range, format, priority
    - Publicar en cola estándar por defecto
    - _Requisitos: 1.3, 6.1_

  - [ ]* 4.2 Escribir test de propiedad para publicación SQS
    - **Propiedad 3: Creación de trabajo publica mensaje SQS completo**
    - **Valida: Requisitos 1.3, 6.1**

- [x] 5. Checkpoint - Verificar capa de datos y servicios base
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

- [x] 6. Endpoints de trabajos (API REST)
  - [x] 6.1 Implementar schemas Pydantic de trabajos
    - Crear `backend/app/jobs/schemas.py` con modelos: `DateRange` (con validador start_date < end_date), `JobCreateRequest` (report_type, date_range, format), `JobCreateResponse`, `JobResponse`, `JobListResponse`
    - _Requisitos: 1.1, 1.2, 5.1, 5.2_

  - [x] 6.2 Implementar servicio de trabajos
    - Crear `backend/app/jobs/service.py` con lógica de negocio: `create_job` (crear en DynamoDB + publicar en SQS), `get_job` (con verificación de propiedad), `list_user_jobs` (paginado)
    - Si la publicación en SQS falla, marcar trabajo como FAILED y retornar 503
    - _Requisitos: 1.1, 1.3, 1.5, 2.1, 2.2, 2.3, 3.1_

  - [x] 6.3 Implementar router de trabajos
    - Crear `backend/app/jobs/router.py` con endpoints: POST `/jobs` (201), GET `/jobs` (200 paginado), GET `/jobs/{job_id}` (200)
    - Todos los endpoints protegidos con middleware JWT
    - Retornar 403 si el usuario consulta un trabajo ajeno, 404 si no existe
    - _Requisitos: 1.1, 1.2, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_

  - [ ]* 6.4 Escribir tests de propiedad para creación y consulta de trabajos
    - **Propiedad 1: Creación de trabajo válida retorna PENDING**
    - **Propiedad 2: Entrada inválida retorna 422 con detalle del campo**
    - **Propiedad 5: Consulta de trabajo retorna estado completo para el propietario**
    - **Propiedad 6: Aislamiento de datos entre usuarios**
    - **Valida: Requisitos 1.1, 1.2, 2.1, 2.2, 5.2**

  - [ ]* 6.5 Escribir tests de propiedad para listado paginado
    - **Propiedad 7: Listado de trabajos contiene exclusivamente trabajos del usuario**
    - **Propiedad 8: Paginación correcta con metadatos**
    - **Valida: Requisitos 3.1, 3.2, 3.3, 3.4**

- [x] 7. Manejo centralizado de errores
  - [x] 7.1 Implementar exception handlers globales
    - Crear `backend/app/errors/handlers.py` con exception handlers para: `RequestValidationError` (422), `HTTPException` (4xx), excepciones genéricas (500)
    - Todas las respuestas de error usan el modelo `ErrorResponse` uniforme con campos `detail` y `field` opcional
    - Registrar errores internos en log con nivel ERROR incluyendo traceback completo
    - No exponer detalles internos en respuestas 500
    - _Requisitos: 5.2, 5.3, 5.4, 5.5_

  - [x] 7.2 Crear aplicación FastAPI principal con middleware y handlers
    - Crear `backend/app/main.py` con la app FastAPI, registrar routers (auth, jobs), exception handlers globales y middleware
    - Crear `backend/app/dependencies.py` con inyección de dependencias para clientes DB y SQS
    - _Requisitos: 5.5_

- [x] 8. Worker — Consumidor SQS y procesador de reportes
  - [x] 8.1 Implementar consumidor SQS del worker
    - Crear `worker/app/consumer.py` con polling continuo de la cola SQS estándar usando long polling
    - Implementar procesamiento de al menos 2 mensajes en paralelo con asyncio
    - Eliminar mensaje de la cola tras procesamiento exitoso; si falla la eliminación, registrar WARNING
    - _Requisitos: 7.1, 7.5, 7.6, 7.7_

  - [x] 8.2 Implementar procesador de reportes (simulado)
    - Crear `worker/app/processor.py` con lógica de generación de reportes simulada (sleep aleatorio entre 5-30 segundos)
    - Actualizar estado a PROCESSING antes de iniciar, luego a COMPLETED con result_url o FAILED con error_message
    - Crear `worker/app/db/client.py` y `worker/app/db/repository.py` para operaciones de actualización de estado
    - _Requisitos: 7.2, 7.3, 7.4_

  - [x] 8.3 Implementar entry point del worker
    - Crear `worker/app/main.py` como punto de entrada que inicie el loop de consumo asyncio
    - _Requisitos: 7.1_

  - [ ]* 8.4 Escribir tests de propiedad para transiciones de estado del worker
    - **Propiedad 12: Transiciones de estado del Worker**
    - **Propiedad 13: Mensaje SQS eliminado tras procesamiento exitoso**
    - **Propiedad 14: updated_at se actualiza en cada modificación**
    - **Valida: Requisitos 7.2, 7.3, 7.4, 7.6, 8.3**

- [x] 9. Checkpoint - Verificar flujo completo backend + worker
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

- [x] 10. Containerización y entorno de desarrollo local
  - [x] 10.1 Crear Dockerfiles del backend y worker
    - Crear `backend/Dockerfile` con build multi-stage, imagen base Python slim, usuario no-root, `.dockerignore`
    - Crear `worker/Dockerfile` con la misma estrategia
    - _Requisitos: 14.1, 14.2, 14.3, 14.4, 14.5_

  - [x] 10.2 Crear Dockerfile del frontend
    - Crear `frontend/Dockerfile` con build multi-stage: etapa de build con Node y etapa de producción con Nginx
    - _Requisitos: 9.1_

  - [x] 10.3 Crear docker-compose.yml y script de inicialización de LocalStack
    - Crear `docker-compose.yml` con servicios: backend, worker, frontend, localstack
    - Crear `infra/localstack/init-aws.sh` que cree la tabla DynamoDB (con GSI), tabla users (con GSI), colas SQS estándar y DLQ
    - Crear `.env.example` con todas las variables de entorno documentadas
    - Configurar reintentos de conexión a LocalStack (máximo 30 segundos)
    - _Requisitos: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 11. Frontend React — Autenticación y formulario de reportes
  - [x] 11.1 Implementar cliente HTTP y hook de autenticación
    - Crear `frontend/src/api/client.ts` con cliente HTTP (fetch) que incluya JWT en headers automáticamente
    - Crear `frontend/src/hooks/useAuth.ts` con lógica de login, registro, almacenamiento de token y redirección
    - Crear `frontend/src/components/LoginForm.tsx` con formulario de username/password
    - Crear `frontend/src/pages/LoginPage.tsx`
    - _Requisitos: 9.8, 4.1_

  - [x] 11.2 Implementar formulario de creación de reportes
    - Crear `frontend/src/components/JobForm.tsx` con campos: report_type (selector), date_range (fecha inicio/fin), format (selector CSV/PDF/JSON)
    - Validación client-side con mensajes de error inline (sin alert() nativo)
    - Enviar POST a /jobs al submit y mostrar notificación de confirmación
    - _Requisitos: 9.1, 9.2, 9.3_

  - [x] 11.3 Implementar lista de trabajos y badges de estado
    - Crear `frontend/src/components/JobList.tsx` con lista de trabajos del usuario
    - Crear `frontend/src/components/JobStatusBadge.tsx` con badges de color por estado
    - Crear `frontend/src/hooks/useJobs.ts` con lógica de CRUD y polling cada 5 segundos
    - _Requisitos: 9.4, 9.5_

  - [x] 11.4 Implementar componentes de notificación, layout y página principal
    - Crear `frontend/src/components/Toast.tsx` para notificaciones visuales de error/éxito (sin alert() nativo)
    - Crear `frontend/src/components/Layout.tsx` con layout responsive (desktop 1024px+, móvil 320px+)
    - Crear `frontend/src/pages/DashboardPage.tsx` integrando JobForm, JobList y Toast
    - Crear `frontend/src/App.tsx` con routing entre LoginPage y DashboardPage
    - _Requisitos: 9.6, 9.7_

  - [ ]* 11.5 Escribir tests de propiedad para badges de estado del frontend
    - **Propiedad 25: Badges de estado con colores correctos**
    - **Valida: Requisitos 9.4**

- [x] 12. Infraestructura Terraform para producción
  - [x] 12.1 Crear configuración Terraform base
    - Crear `infra/terraform/main.tf` con provider AWS y backend de estado
    - Crear `infra/terraform/variables.tf` con variables de configuración (región, nombre del proyecto, key pair, etc.)
    - Crear `infra/terraform/outputs.tf` con outputs: URL pública, ARNs de recursos
    - _Requisitos: 11.1_

  - [x] 12.2 Crear recursos DynamoDB y SQS con Terraform
    - Crear `infra/terraform/dynamodb.tf` con tabla `jobs` (PK: job_id, GSI: user-jobs-index) y tabla `users` (PK: user_id, GSI: username-index), capacidad provisionada dentro del free tier (25 RCU/WCU)
    - Crear `infra/terraform/sqs.tf` con colas estándar + DLQ (visibility timeout 30s, retención 4 días cola principal, 14 días DLQ, max receives 3)
    - _Requisitos: 6.2, 6.3, 6.4, 6.5, 8.4, 8.5, 11.3, 11.4_

  - [x] 12.3 Crear recursos de cómputo EC2 y red con Terraform
    - Crear `infra/terraform/compute.tf` con instancia EC2 t2.micro, VPC, Security Group (puertos 80, 443, 22), user data para instalar Docker y Docker Compose
    - Crear `infra/terraform/iam.tf` con rol IAM para EC2 con permisos a DynamoDB y SQS
    - _Requisitos: 11.2, 11.3_

- [x] 13. Pipeline CI/CD con GitHub Actions
  - [x] 13.1 Crear workflow de despliegue
    - Crear `.github/workflows/deploy.yml` con pipeline que: ejecute tests (pytest + vitest), construya imágenes Docker, despliegue a EC2 via SSH
    - Usar GitHub Secrets para credenciales AWS (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, EC2_SSH_KEY)
    - Detener el flujo si alguna prueba falla
    - Registrar URL pública en logs del pipeline al completar
    - _Requisitos: 12.1, 12.2, 12.3, 12.5_

  - [x] 13.2 Crear documentación del proyecto
    - Crear `README.md` con instrucciones de configuración, comandos de desarrollo local, URL de producción y badge de CI/CD
    - Crear `TECHNICAL_DOCS.md` con diagrama de arquitectura, tabla de servicios AWS, decisiones de diseño
    - Crear `SKILL.md` como archivo de contexto para agentes de IA
    - Crear `AI_WORKFLOW.md` con evidencia del uso de herramientas de IA
    - _Requisitos: 12.4, 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 14. Checkpoint - Verificar sistema completo core
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

- [x] 15. (Bonus B1) Colas de prioridad
  - [x] 15.1 Implementar enrutamiento de mensajes por prioridad
    - Modificar `backend/app/queue/publisher.py` para publicar en cola de alta prioridad cuando `priority="high"`
    - Modificar `worker/app/consumer.py` para consumir de la cola de alta prioridad antes que la estándar
    - Agregar campo `priority` al schema `JobCreateRequest` con valor por defecto "standard"
    - Actualizar `infra/localstack/init-aws.sh` y `infra/terraform/sqs.tf` para crear ambas colas con sus DLQs
    - _Requisitos: 15.1, 15.2, 15.3, 15.4_

  - [ ]* 15.2 Escribir tests de propiedad para colas de prioridad
    - **Propiedad 15: Enrutamiento de mensajes por prioridad**
    - **Propiedad 16: Consumo prioritario de colas**
    - **Valida: Requisitos 15.1, 15.2, 15.3**

- [x] 16. (Bonus B2) Patrón Circuit Breaker en Worker
  - [x] 16.1 Implementar Circuit Breaker
    - Crear `worker/app/circuit_breaker.py` con clase `CircuitBreaker` con estados: closed, open, half_open
    - Abrir circuito tras 5 fallos consecutivos, pausar 60 segundos
    - Transicionar a half-open tras expirar el timeout, probar 1 mensaje
    - Cerrar circuito si el mensaje de prueba es exitoso, reabrir si falla
    - Registrar estado del circuito en log con nivel WARNING cuando se abre
    - Integrar con `worker/app/consumer.py`
    - _Requisitos: 16.1, 16.2, 16.3, 16.4, 16.5_

  - [ ]* 16.2 Escribir tests de propiedad para Circuit Breaker
    - **Propiedad 17: Circuit Breaker se abre tras fallos consecutivos**
    - **Propiedad 18: Circuit Breaker — transición half-open y recuperación**
    - **Valida: Requisitos 16.1, 16.2, 16.3, 16.4, 16.5**

- [x] 17. (Bonus B3) Notificaciones en Tiempo Real con SSE
  - [x] 17.1 Implementar endpoint SSE y hook del frontend
    - Crear `backend/app/stream/router.py` con endpoint GET `/stream/jobs` que retorne un stream SSE para el usuario autenticado
    - Crear `backend/app/stream/service.py` con lógica de polling de DynamoDB y emisión de eventos SSE cuando cambia el estado de un trabajo
    - Crear `frontend/src/hooks/useSSE.ts` con conexión EventSource, reconexión automática y fallback a polling tras 30 segundos
    - Modificar `frontend/src/hooks/useJobs.ts` para usar SSE cuando esté disponible en lugar de polling
    - Registrar router SSE en `backend/app/main.py`
    - _Requisitos: 17.1, 17.2, 17.3, 17.4_

  - [ ]* 17.2 Escribir test de propiedad para eventos SSE
    - **Propiedad 19: Eventos SSE emitidos en cambios de estado**
    - **Valida: Requisitos 17.2**

- [x] 18. (Bonus B4) Reintentos con Backoff Exponencial
  - [x] 18.1 Implementar retry con backoff exponencial y jitter
    - Crear `worker/app/retry.py` con función `retry_with_backoff` que implemente intervalos exponenciales (1s, 2s, 4s) con jitter aleatorio ±500ms, máximo 3 reintentos
    - Registrar cada intento en log con nivel INFO (número de intento y tiempo de espera)
    - Marcar trabajo como FAILED tras agotar reintentos y permitir que el mensaje vaya a DLQ
    - Integrar con `worker/app/consumer.py`
    - _Requisitos: 18.1, 18.2, 18.3, 18.4_

  - [ ]* 18.2 Escribir tests de propiedad para backoff exponencial
    - **Propiedad 20: Backoff exponencial con jitter en reintentos**
    - **Propiedad 21: Agotamiento de reintentos marca trabajo como FAILED**
    - **Valida: Requisitos 18.1, 18.2, 18.3**

- [x] 19. (Bonus B5) Observabilidad
  - [x] 19.1 Implementar logging estructurado y métricas
    - Crear `backend/app/observability/logging.py` con configuración de logging JSON estructurado (campos: timestamp, level, message, request_id)
    - Crear `backend/app/observability/metrics.py` con métricas en memoria: contadores de trabajos creados/completados/fallidos, tiempo promedio de procesamiento
    - Crear `worker/app/observability/logging.py` con la misma configuración de logging JSON
    - _Requisitos: 19.1, 19.3, 19.4_

  - [x] 19.2 Implementar endpoint de health check
    - Crear endpoint GET `/health` en `backend/app/main.py` que verifique conectividad con DynamoDB y SQS
    - Retornar 200 con `{status: "healthy", dynamodb: "ok", sqs: "ok"}` si todo está operativo, o 503 si algún servicio falla
    - _Requisitos: 19.2_

  - [ ]* 19.3 Escribir tests de propiedad para observabilidad
    - **Propiedad 22: Logging JSON estructurado con campos requeridos**
    - **Propiedad 23: Métricas de ciclo de vida de trabajos**
    - **Valida: Requisitos 19.1, 19.3, 19.4**

- [x] 20. (Bonus B6) Suite de Pruebas Avanzada
  - [x] 20.1 Implementar pruebas unitarias y de integración con cobertura mínima 70%
    - Crear pruebas unitarias para todos los endpoints del API en `backend/tests/unit/`
    - Crear pruebas de integración del flujo completo (crear → procesar → completar) en `backend/tests/integration/`
    - Crear pruebas de simulación de fallos (SQS down, DynamoDB down) en `backend/tests/integration/test_failure_scenarios.py`
    - Configurar pytest-cov para generar reporte de cobertura y fallar si < 70%
    - _Requisitos: 20.1, 20.2, 20.3, 20.4_

- [x] 21. Checkpoint final - Verificar sistema completo con bonus
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido.
- Las tareas bonus (15-20) corresponden a los requisitos B1-B6 y son completamente opcionales.
- Cada tarea referencia los requisitos específicos para trazabilidad.
- Los checkpoints permiten validación incremental del sistema.
- Los tests de propiedad validan propiedades universales de correctitud definidas en el documento de diseño.
- Los tests unitarios validan ejemplos específicos y casos borde.
