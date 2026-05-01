# Documento de Requisitos — Sistema de Procesamiento Asíncrono de Reportes

## Introducción

Sistema completo de procesamiento asíncrono de reportes para una plataforma SaaS de analítica. Los usuarios solicitan reportes de datos bajo demanda; dado que la generación toma entre 5 segundos y varios minutos, el procesamiento se realiza de forma asíncrona mediante una cola de mensajes y workers concurrentes. El sistema incluye backend (Python/FastAPI), cola de mensajes (AWS SQS), workers concurrentes, persistencia (AWS DynamoDB), frontend (React), infraestructura como código, pipeline CI/CD y documentación completa. Todo el sistema debe operar dentro del nivel gratuito de AWS (cero cargos) y desplegarse con configuración mínima manual.

## Glosario

- **Sistema_API**: Servidor backend construido con Python y FastAPI que expone los endpoints REST para la gestión de trabajos de reportes.
- **Cola_Mensajes**: Servicio de cola de mensajes AWS SQS utilizado para desacoplar la creación de trabajos de su procesamiento.
- **Cola_DLQ**: Cola de mensajes muertos (Dead Letter Queue) de AWS SQS que recibe mensajes que han fallado repetidamente en su procesamiento.
- **Worker**: Proceso asíncrono que consume mensajes de la Cola_Mensajes y ejecuta la generación de reportes.
- **Base_Datos**: Tabla de AWS DynamoDB utilizada para persistir el estado de los trabajos de reportes.
- **Frontend**: Aplicación web React que permite a los usuarios crear trabajos de reportes, visualizar su estado y consultar resultados.
- **Trabajo**: Entidad que representa una solicitud de generación de reporte, con estados PENDING, PROCESSING, COMPLETED o FAILED.
- **Usuario_Autenticado**: Usuario que ha proporcionado un token JWT válido para acceder a los recursos del sistema.
- **LocalStack**: Emulador local de servicios AWS utilizado para desarrollo sin incurrir en costos.
- **Pipeline_CICD**: Flujo de GitHub Actions que automatiza el despliegue a AWS en cada push a la rama main.
- **IaC**: Infraestructura como Código, scripts de Terraform, CloudFormation o YAML que automatizan la creación de recursos AWS.
- **Nivel_Gratuito_AWS**: Límites del free tier de AWS que permiten operar sin cargos: DynamoDB (25 GB, 25 RCU/WCU), SQS (1M solicitudes/mes), Lambda (1M invocaciones/mes).

## Requisitos

### Requisito 1: Creación de Trabajos de Reporte

**Historia de Usuario:** Como usuario autenticado, quiero crear un trabajo de generación de reporte proporcionando los parámetros necesarios, para que el sistema procese mi solicitud de forma asíncrona.

#### Criterios de Aceptación

1. WHEN el Usuario_Autenticado envía una solicitud POST a /jobs con parámetros válidos (report_type, date_range, format), THE Sistema_API SHALL crear un Trabajo con estado PENDING y retornar un objeto JSON con job_id y status "PENDING" con código HTTP 201.
2. WHEN el Usuario_Autenticado envía una solicitud POST a /jobs con parámetros inválidos, THE Sistema_API SHALL retornar un error de validación con código HTTP 422 y un mensaje descriptivo del campo inválido.
3. WHEN el Sistema_API crea un Trabajo exitosamente, THE Sistema_API SHALL publicar un mensaje en la Cola_Mensajes con el job_id y los parámetros del reporte.
4. WHEN el Sistema_API crea un Trabajo, THE Base_Datos SHALL almacenar el registro con los campos: job_id, user_id, status, report_type, created_at, updated_at y result_url.
5. IF la publicación del mensaje en la Cola_Mensajes falla, THEN THE Sistema_API SHALL marcar el Trabajo como FAILED en la Base_Datos y retornar un error con código HTTP 503.

### Requisito 2: Consulta de Estado de Trabajos

**Historia de Usuario:** Como usuario autenticado, quiero consultar el estado y resultado de un trabajo específico, para saber si mi reporte está listo.

#### Criterios de Aceptación

1. WHEN el Usuario_Autenticado envía una solicitud GET a /jobs/{job_id}, THE Sistema_API SHALL retornar el estado actual del Trabajo incluyendo job_id, status, report_type, created_at, updated_at y result_url con código HTTP 200.
2. WHEN el Usuario_Autenticado consulta un Trabajo que pertenece a otro usuario, THE Sistema_API SHALL retornar un error con código HTTP 403.
3. WHEN el Usuario_Autenticado consulta un job_id que no existe, THE Sistema_API SHALL retornar un error con código HTTP 404 y un mensaje indicando que el Trabajo no fue encontrado.

### Requisito 3: Listado Paginado de Trabajos

**Historia de Usuario:** Como usuario autenticado, quiero listar todos mis trabajos de reporte con paginación, para revisar el historial de mis solicitudes.

#### Criterios de Aceptación

1. WHEN el Usuario_Autenticado envía una solicitud GET a /jobs, THE Sistema_API SHALL retornar una lista paginada de Trabajos pertenecientes exclusivamente al Usuario_Autenticado.
2. THE Sistema_API SHALL retornar un mínimo de 20 Trabajos por página cuando existan suficientes registros.
3. WHEN el Usuario_Autenticado proporciona un parámetro de paginación (cursor o page), THE Sistema_API SHALL retornar la página correspondiente de resultados.
4. THE Sistema_API SHALL incluir en la respuesta metadatos de paginación: total de elementos, página actual y referencia a la siguiente página.

### Requisito 4: Autenticación JWT

**Historia de Usuario:** Como usuario, quiero autenticarme mediante JWT para acceder de forma segura a los endpoints del sistema.

#### Criterios de Aceptación

1. WHEN un usuario envía credenciales válidas (username, password) al endpoint POST /auth/login, THE Sistema_API SHALL retornar un token JWT firmado con una expiración configurable.
2. WHEN un usuario envía credenciales inválidas al endpoint POST /auth/login, THE Sistema_API SHALL retornar un error con código HTTP 401 y un mensaje indicando credenciales inválidas.
3. WHEN una solicitud a un endpoint protegido no incluye un token JWT en el header Authorization, THE Sistema_API SHALL retornar un error con código HTTP 401.
4. WHEN una solicitud incluye un token JWT expirado o con firma inválida, THE Sistema_API SHALL retornar un error con código HTTP 401 y un mensaje descriptivo.
5. THE Sistema_API SHALL extraer el user_id del token JWT para identificar al Usuario_Autenticado en cada solicitud protegida.
6. WHEN un usuario envía una solicitud POST a /auth/register con datos válidos (username, password), THE Sistema_API SHALL crear una cuenta de usuario y retornar un código HTTP 201.

### Requisito 5: Validación y Manejo Centralizado de Errores

**Historia de Usuario:** Como desarrollador, quiero que el sistema valide todas las entradas con Pydantic v2 y maneje errores de forma centralizada, para garantizar respuestas consistentes y seguras.

#### Criterios de Aceptación

1. THE Sistema_API SHALL validar todas las solicitudes entrantes utilizando modelos Pydantic v2.
2. WHEN ocurre un error de validación, THE Sistema_API SHALL retornar una respuesta JSON con código HTTP 422, incluyendo el campo afectado y la descripción del error.
3. WHEN ocurre un error interno no controlado, THE Sistema_API SHALL retornar una respuesta JSON con código HTTP 500 y un mensaje genérico sin exponer detalles internos del sistema.
4. THE Sistema_API SHALL registrar todos los errores internos en el log del servidor con nivel ERROR, incluyendo el traceback completo.
5. THE Sistema_API SHALL utilizar un middleware o exception handler global para capturar y formatear todas las excepciones de forma uniforme.


### Requisito 6: Procesamiento Asíncrono con Cola de Mensajes

**Historia de Usuario:** Como arquitecto del sistema, quiero que los trabajos se procesen de forma asíncrona mediante una cola de mensajes AWS SQS, para desacoplar la creación de trabajos de su ejecución.

#### Criterios de Aceptación

1. WHEN el Sistema_API crea un Trabajo, THE Sistema_API SHALL publicar un mensaje en la Cola_Mensajes de AWS SQS con el job_id, user_id, report_type, date_range y format.
2. THE Cola_Mensajes SHALL tener configurada una Cola_DLQ asociada para recibir mensajes que fallen después de 3 intentos de procesamiento.
3. WHEN un mensaje permanece en la Cola_Mensajes sin ser procesado durante más de 30 segundos, THE Cola_Mensajes SHALL hacer el mensaje visible nuevamente para otro Worker.
4. THE Cola_Mensajes SHALL retener los mensajes durante un máximo de 4 días antes de descartarlos.
5. THE Cola_DLQ SHALL retener los mensajes fallidos durante un máximo de 14 días para permitir análisis posterior.

### Requisito 7: Workers Concurrentes

**Historia de Usuario:** Como arquitecto del sistema, quiero que múltiples workers procesen mensajes en paralelo, para maximizar el throughput del sistema.

#### Criterios de Aceptación

1. THE Worker SHALL consumir mensajes de la Cola_Mensajes de forma continua mediante polling.
2. WHEN el Worker recibe un mensaje, THE Worker SHALL actualizar el estado del Trabajo a PROCESSING en la Base_Datos antes de iniciar la generación del reporte.
3. WHEN el Worker completa la generación del reporte, THE Worker SHALL actualizar el estado del Trabajo a COMPLETED en la Base_Datos e incluir el result_url.
4. IF el Worker falla durante la generación del reporte, THEN THE Worker SHALL actualizar el estado del Trabajo a FAILED en la Base_Datos con un mensaje de error descriptivo.
5. THE Worker SHALL procesar al menos 2 mensajes en paralelo utilizando concurrencia asíncrona (asyncio).
6. WHEN el Worker procesa un mensaje exitosamente, THE Worker SHALL eliminar el mensaje de la Cola_Mensajes.
7. IF el Worker no puede eliminar el mensaje de la Cola_Mensajes después de procesarlo, THEN THE Worker SHALL registrar el error en el log con nivel WARNING.

### Requisito 8: Persistencia en DynamoDB

**Historia de Usuario:** Como arquitecto del sistema, quiero almacenar el estado de los trabajos en AWS DynamoDB, para tener persistencia escalable dentro del nivel gratuito de AWS.

#### Criterios de Aceptación

1. THE Base_Datos SHALL almacenar cada Trabajo con los campos: job_id (partition key), user_id, status, report_type, created_at, updated_at y result_url.
2. THE Base_Datos SHALL tener un índice secundario global (GSI) con user_id como partition key y created_at como sort key para consultas eficientes de listado por usuario.
3. WHEN se actualiza un Trabajo, THE Base_Datos SHALL actualizar automáticamente el campo updated_at con la marca de tiempo actual.
4. THE IaC SHALL incluir un script de inicialización que cree la tabla y el GSI en DynamoDB.
5. THE Base_Datos SHALL operar en modo de capacidad bajo demanda (on-demand) o con capacidad provisionada dentro de los límites del Nivel_Gratuito_AWS (25 RCU y 25 WCU).

### Requisito 9: Frontend React

**Historia de Usuario:** Como usuario, quiero una interfaz web para crear reportes, ver el estado de mis trabajos y acceder a los resultados, para interactuar con el sistema de forma visual.

#### Criterios de Aceptación

1. THE Frontend SHALL mostrar un formulario con los campos: report_type (selector), date_range (fecha inicio y fin) y format (selector con opciones CSV, PDF, JSON).
2. WHEN el usuario envía el formulario con datos válidos, THE Frontend SHALL enviar una solicitud POST a /jobs y mostrar una notificación visual de confirmación.
3. WHEN el usuario envía el formulario con datos inválidos, THE Frontend SHALL mostrar mensajes de error junto a los campos afectados sin utilizar alert() nativo del navegador.
4. THE Frontend SHALL mostrar una lista de Trabajos del usuario con badges de color según el estado: amarillo para PENDING, azul para PROCESSING, verde para COMPLETED y rojo para FAILED.
5. THE Frontend SHALL actualizar automáticamente el estado de los Trabajos visibles mediante polling cada 5 segundos sin requerir recarga manual de la página.
6. THE Frontend SHALL ser responsive y funcionar correctamente en pantallas de escritorio (1024px o más) y dispositivos móviles (320px o más).
7. WHEN el Sistema_API retorna un error, THE Frontend SHALL mostrar un componente visual de error (toast o banner) sin utilizar alert() nativo del navegador.
8. THE Frontend SHALL incluir una pantalla de login que solicite username y password, y almacenar el token JWT para solicitudes autenticadas.

### Requisito 10: Entorno de Desarrollo con LocalStack

**Historia de Usuario:** Como desarrollador, quiero levantar todo el entorno de desarrollo con un solo comando docker compose up, para trabajar sin depender de AWS real y sin incurrir en costos.

#### Criterios de Aceptación

1. THE IaC SHALL incluir un archivo docker-compose.yml que levante todos los servicios: Sistema_API, Worker, Frontend, LocalStack y cualquier dependencia.
2. WHEN el desarrollador ejecuta "docker compose up", THE IaC SHALL inicializar automáticamente los recursos de LocalStack (tabla DynamoDB, colas SQS) sin intervención manual.
3. THE IaC SHALL incluir un archivo .env.example con todas las variables de entorno necesarias, sin incluir credenciales reales.
4. THE IaC SHALL configurar LocalStack para emular los servicios AWS SQS y DynamoDB utilizados por el sistema.
5. IF LocalStack no está disponible al iniciar el Sistema_API, THEN THE Sistema_API SHALL reintentar la conexión durante un máximo de 30 segundos antes de fallar con un mensaje descriptivo.

### Requisito 11: Despliegue en AWS de Producción

**Historia de Usuario:** Como evaluador, quiero acceder al sistema desplegado en una URL pública de AWS, para verificar que funciona en un entorno real.

#### Criterios de Aceptación

1. THE IaC SHALL incluir scripts de infraestructura como código (Terraform o CloudFormation) que creen todos los recursos AWS necesarios para producción.
2. THE IaC SHALL desplegar el Sistema_API en un servicio AWS accesible públicamente mediante una URL HTTPS.
3. THE IaC SHALL configurar todos los recursos de producción dentro de los límites del Nivel_Gratuito_AWS para garantizar cero cargos.
4. THE IaC SHALL utilizar exclusivamente servicios elegibles para el nivel gratuito: DynamoDB, SQS, Lambda o ECS (según aplique), API Gateway o ALB.
5. WHEN el despliegue se completa, THE Pipeline_CICD SHALL registrar la URL pública de producción en los logs del pipeline.

### Requisito 12: Pipeline CI/CD con GitHub Actions

**Historia de Usuario:** Como desarrollador, quiero que el sistema se despliegue automáticamente a AWS cuando hago push a la rama main, para mantener el entorno de producción actualizado.

#### Criterios de Aceptación

1. WHEN se realiza un push a la rama main, THE Pipeline_CICD SHALL ejecutar automáticamente el flujo de despliegue a AWS.
2. THE Pipeline_CICD SHALL ejecutar las pruebas del proyecto antes del despliegue y detener el flujo si alguna prueba falla.
3. THE Pipeline_CICD SHALL utilizar secretos de GitHub (GitHub Secrets) para las credenciales de AWS, sin exponer credenciales en el código fuente.
4. THE Pipeline_CICD SHALL incluir un badge de estado en el archivo README.md que refleje el resultado del último despliegue.
5. IF el despliegue falla, THEN THE Pipeline_CICD SHALL notificar el error en los logs del workflow con un mensaje descriptivo.

### Requisito 13: Documentación del Proyecto

**Historia de Usuario:** Como evaluador, quiero documentación completa del proyecto para entender la arquitectura, decisiones de diseño y cómo configurar el sistema.

#### Criterios de Aceptación

1. THE Sistema_API SHALL incluir un archivo TECHNICAL_DOCS.md con: diagrama de arquitectura (texto o imagen), tabla de servicios AWS utilizados, decisiones de diseño y guías de configuración.
2. THE Sistema_API SHALL incluir un archivo SKILL.md que sirva como archivo de contexto para agentes de IA, describiendo la estructura del proyecto y convenciones.
3. THE Sistema_API SHALL incluir un archivo AI_WORKFLOW.md con evidencia del uso de herramientas de IA durante el desarrollo.
4. THE Sistema_API SHALL incluir un archivo README.md con instrucciones de configuración, comandos para desarrollo local, URL de producción y badge de CI/CD.
5. THE IaC SHALL incluir un archivo .env.example documentando cada variable de entorno con su descripción y valor por defecto cuando aplique.

### Requisito 14: Containerización del Backend

**Historia de Usuario:** Como desarrollador, quiero que el backend tenga un Dockerfile optimizado, para facilitar el despliegue tanto local como en AWS.

#### Criterios de Aceptación

1. THE Sistema_API SHALL incluir un Dockerfile que construya una imagen funcional del backend con todas las dependencias.
2. THE Dockerfile SHALL utilizar una imagen base de Python slim para minimizar el tamaño de la imagen.
3. THE Dockerfile SHALL utilizar un build multi-stage o instalación de dependencias en una capa separada para aprovechar la caché de Docker.
4. WHEN se construye la imagen Docker, THE Dockerfile SHALL no incluir archivos innecesarios (tests, documentación, archivos de configuración local) mediante un archivo .dockerignore.
5. THE Dockerfile SHALL ejecutar la aplicación con un usuario no-root por seguridad.


### Requisito 15 (Bonus B1): Colas de Prioridad

**Historia de Usuario:** Como usuario, quiero poder marcar un reporte como de alta prioridad, para que se procese antes que los reportes estándar.

#### Criterios de Aceptación

1. WHEN el Usuario_Autenticado crea un Trabajo con prioridad "high", THE Sistema_API SHALL publicar el mensaje en una Cola_Mensajes de alta prioridad separada.
2. WHEN el Usuario_Autenticado crea un Trabajo con prioridad "standard" o sin especificar prioridad, THE Sistema_API SHALL publicar el mensaje en la Cola_Mensajes estándar.
3. THE Worker SHALL consumir mensajes de la cola de alta prioridad antes de consumir mensajes de la cola estándar.
4. THE IaC SHALL crear ambas colas (alta prioridad y estándar) con sus respectivas Cola_DLQ.

### Requisito 16 (Bonus B2): Patrón Circuit Breaker en Worker

**Historia de Usuario:** Como arquitecto del sistema, quiero implementar el patrón Circuit Breaker en los workers, para evitar que fallos en cascada degraden todo el sistema.

#### Criterios de Aceptación

1. WHEN el Worker detecta 5 fallos consecutivos en el procesamiento de mensajes, THE Worker SHALL abrir el circuito y dejar de consumir mensajes durante 60 segundos.
2. WHILE el circuito está abierto, THE Worker SHALL rechazar nuevos mensajes y registrar el estado en el log con nivel WARNING.
3. WHEN el período de espera del circuito abierto expira, THE Worker SHALL pasar a estado semi-abierto y procesar un mensaje de prueba.
4. WHEN el mensaje de prueba en estado semi-abierto se procesa exitosamente, THE Worker SHALL cerrar el circuito y reanudar el consumo normal de mensajes.
5. IF el mensaje de prueba en estado semi-abierto falla, THEN THE Worker SHALL reabrir el circuito por otro período de 60 segundos.

### Requisito 17 (Bonus B3): Notificaciones en Tiempo Real con SSE

**Historia de Usuario:** Como usuario, quiero recibir actualizaciones en tiempo real del estado de mis reportes sin necesidad de polling, para una experiencia más fluida.

#### Criterios de Aceptación

1. THE Sistema_API SHALL exponer un endpoint GET /stream/jobs que retorne un stream de Server-Sent Events (SSE) para usuarios autenticados.
2. WHEN el estado de un Trabajo del Usuario_Autenticado cambia, THE Sistema_API SHALL enviar un evento SSE con el job_id, el nuevo status y el updated_at.
3. WHEN el Frontend establece una conexión SSE, THE Frontend SHALL utilizar los eventos SSE en lugar del polling para actualizar el estado de los Trabajos.
4. IF la conexión SSE se pierde, THEN THE Frontend SHALL reconectar automáticamente utilizando el mecanismo nativo de EventSource y utilizar polling como fallback si la reconexión falla después de 30 segundos.

### Requisito 18 (Bonus B4): Reintentos con Backoff Exponencial

**Historia de Usuario:** Como arquitecto del sistema, quiero que los workers reintenten operaciones fallidas con backoff exponencial, para manejar fallos transitorios sin sobrecargar los servicios.

#### Criterios de Aceptación

1. WHEN el Worker falla al procesar un mensaje, THE Worker SHALL reintentar la operación con intervalos de espera exponenciales: 1s, 2s, 4s hasta un máximo de 3 reintentos.
2. WHEN el Worker agota los 3 reintentos, THE Worker SHALL marcar el Trabajo como FAILED y permitir que el mensaje sea enviado a la Cola_DLQ.
3. THE Worker SHALL agregar jitter aleatorio (±500ms) a cada intervalo de reintento para evitar thundering herd.
4. THE Worker SHALL registrar cada intento de reintento en el log con nivel INFO, incluyendo el número de intento y el tiempo de espera.

### Requisito 19 (Bonus B5): Observabilidad

**Historia de Usuario:** Como operador del sistema, quiero logging estructurado, métricas y un endpoint de salud, para monitorear el estado del sistema en producción.

#### Criterios de Aceptación

1. THE Sistema_API SHALL emitir logs en formato JSON estructurado con los campos: timestamp, level, message, request_id y contexto adicional relevante.
2. THE Sistema_API SHALL exponer un endpoint GET /health que retorne el estado de conectividad con la Base_Datos y la Cola_Mensajes con código HTTP 200 si todo está operativo o 503 si algún servicio no responde.
3. THE Sistema_API SHALL registrar métricas de: número de trabajos creados, trabajos completados, trabajos fallidos y tiempo promedio de procesamiento.
4. THE Worker SHALL emitir logs en formato JSON estructurado con los mismos campos que el Sistema_API.

### Requisito 20 (Bonus B6): Suite de Pruebas Avanzada

**Historia de Usuario:** Como desarrollador, quiero una suite de pruebas con cobertura mínima del 70%, para garantizar la calidad y estabilidad del sistema.

#### Criterios de Aceptación

1. THE Sistema_API SHALL incluir pruebas unitarias para todos los endpoints de la API con al menos 70% de cobertura de código.
2. THE Sistema_API SHALL incluir pruebas de integración que verifiquen el flujo completo: creación de trabajo, publicación en cola, procesamiento por worker y actualización de estado.
3. THE Sistema_API SHALL incluir pruebas de simulación de fallos que verifiquen el comportamiento del sistema cuando la Cola_Mensajes o la Base_Datos no están disponibles.
4. WHEN se ejecutan las pruebas, THE Pipeline_CICD SHALL generar un reporte de cobertura y fallar si la cobertura es inferior al 70%.
