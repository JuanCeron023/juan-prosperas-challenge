# AI Workflow — Evidencia de Uso de Herramientas de IA

## Resumen 

Este proyecto fue desarrollado con asistencia de herramientas de IA (Kiro — AI-powered development environment) siguiendo un flujo de trabajo spec-driven. La IA participó en todas las fases del desarrollo: diseño de arquitectura, generación de código, testing y documentación.

## Herramientas de IA Utilizadas

| Herramienta | Propósito | Fase |
|-------------|-----------|------|
| **Kiro** | Desarrollo asistido por IA con specs | Todas las fases |
| **Kiro Specs** | Generación de requisitos, diseño y plan de tareas | Planificación |
| **Kiro Task Execution** | Implementación guiada por tareas | Desarrollo |

## Flujo de Trabajo con IA

### Fase 1: Especificación y Diseño

La IA asistió en la creación de documentos de especificación estructurados:

1. **`requirements.md`** — 20 requisitos funcionales con criterios de aceptación formales (formato WHEN/THEN/SHALL)
2. **`design.md`** — Documento de diseño técnico con:
   - Diagramas de arquitectura (Mermaid)
   - Interfaces de componentes (Python + TypeScript)
   - Modelos de datos (DynamoDB)
   - 25 propiedades de correctitud para testing
   - Estrategia de manejo de errores
   - Estrategia de testing dual (unitarios + property-based)
3. **`tasks.md`** — Plan de implementación incremental con 21 tareas y sub-tareas

### Fase 2: Implementación

La IA generó código para cada componente siguiendo el plan de tareas:

- **Backend API (FastAPI):** Routers, services, schemas, middleware JWT, exception handlers
- **Worker (asyncio):** Consumer SQS, processor, circuit breaker, retry con backoff
- **Frontend (React):** Componentes, hooks, páginas, cliente HTTP
- **Infraestructura:** Terraform (DynamoDB, SQS, EC2, IAM), Docker Compose, LocalStack init
- **CI/CD:** GitHub Actions workflow

### Fase 3: Testing

La IA generó tests siguiendo la estrategia dual definida en el diseño:

- **Tests unitarios:** Verificación de ejemplos específicos y edge cases
- **Tests de propiedades (hypothesis):** Verificación de invariantes universales
- **Tests de integración:** Flujos completos end-to-end con moto (AWS mocks)

### Fase 4: Documentación

La IA generó documentación técnica completa:

- `README.md` — Guía de inicio rápido y comandos
- `TECHNICAL_DOCS.md` — Arquitectura, decisiones de diseño, modelos de datos
- `SKILL.md` — Contexto para agentes de IA
- `AI_WORKFLOW.md` — Este archivo

## Evidencia de Asistencia de IA por Componente

### Arquitectura y Diseño
- Selección de servicios AWS dentro del free tier
- Diseño del patrón productor-consumidor con SQS
- Definición de modelos de datos DynamoDB con GSIs
- Diseño de la estrategia de resiliencia (DLQ, Circuit Breaker, Backoff)
- Elección de SSE sobre WebSocket para notificaciones

### Backend
- Estructura modular con separación de responsabilidades (router/service/repository)
- Implementación de autenticación JWT stateless
- Validación con Pydantic v2 y model validators
- Manejo centralizado de errores con exception handlers globales
- Cliente DynamoDB con endpoint configurable (LocalStack/AWS)

### Worker
- Diseño del loop de consumo con asyncio y semáforo de concurrencia
- Implementación del patrón Circuit Breaker con estados (closed/open/half-open)
- Backoff exponencial con jitter para evitar thundering herd
- Gestión de transiciones de estado del trabajo

### Frontend
- Arquitectura basada en hooks personalizados (useAuth, useJobs, useSSE)
- Cliente HTTP con interceptor JWT automático
- Componentes responsive con validación client-side
- Sistema de notificaciones Toast (sin alert() nativo)
- Polling con fallback desde SSE

### Infraestructura
- Terraform modules para DynamoDB, SQS, EC2, IAM
- Docker multi-stage builds optimizados
- Docker Compose para orquestación local con LocalStack
- Script de inicialización de recursos AWS locales
- Pipeline CI/CD con GitHub Actions

## Decisiones Tomadas con Asistencia de IA

| Decisión | Contexto | Resultado |
|----------|----------|-----------|
| EC2 vs ECS/Lambda | Optimizar para free tier | EC2 t2.micro con Docker Compose |
| SQS vs RabbitMQ | Simplicidad + free tier | SQS con DLQ nativa |
| SSE vs WebSocket | Notificaciones unidireccionales | SSE con fallback a polling |
| Pydantic v2 vs marshmallow | Integración con FastAPI | Pydantic v2 nativo |
| hypothesis vs quickcheck | PBT en Python | hypothesis (ecosistema Python) |
| LocalStack vs moto (dev) | Desarrollo local completo | LocalStack (Docker Compose) |
| moto vs LocalStack (tests) | Tests en CI sin Docker | moto (in-process, rápido) |

## Métricas del Proyecto

| Métrica | Valor |
|---------|-------|
| Requisitos funcionales | 20 (14 core + 6 bonus) |
| Criterios de aceptación | 80+ |
| Propiedades de correctitud | 25 |
| Tareas de implementación | 21 (con sub-tareas) |
| Servicios AWS utilizados | 5 (DynamoDB, SQS, EC2, ECR, CloudWatch) |
| Componentes del sistema | 4 (API, Worker, Frontend, Infra) |

## Beneficios del Flujo Spec-Driven con IA

1. **Trazabilidad completa:** Cada línea de código se vincula a un requisito específico
2. **Consistencia:** La IA mantiene coherencia entre diseño, implementación y tests
3. **Velocidad:** Generación rápida de boilerplate y código repetitivo
4. **Calidad:** Tests de propiedades verifican invariantes que los tests manuales podrían omitir
5. **Documentación:** Generada como parte del flujo, no como afterthought
