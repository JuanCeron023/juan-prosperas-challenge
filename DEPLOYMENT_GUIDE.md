# Guía Completa de Despliegue y Pruebas


## Índice


1. [Probar localmente](#1-probar-localmente)
2. [Preparar cuenta AWS](#2-preparar-cuenta-aws)
3. [Crear infraestructura con Terraform](#3-crear-infraestructura-con-terraform)
4. [Subir a GitHub](#4-subir-a-github)
5. [Configurar GitHub Secrets](#5-configurar-github-secrets)
6. [Primer despliegue](#6-primer-despliegue)
7. [Verificar que todo funciona](#7-verificar-que-todo-funciona)
8. [Crear usuario IAM para revisión](#8-crear-usuario-iam-para-revisión)
9. [Limpieza (después de la evaluación)](#9-limpieza-después-de-la-evaluación)


---


## 1. Probar localmente


Antes de tocar AWS, verifica que todo funciona en local.


### Requisitos previos
- Docker Desktop instalado y corriendo
- Docker Compose v2+
- Node.js 18+ (solo si quieres correr tests del frontend fuera de Docker)
- Python 3.11+ (solo si quieres correr tests del backend fuera de Docker)


### Levantar el entorno completo


```bash
# Copiar variables de entorno
cp .env.example .env


# Levantar todo (LocalStack + Backend + Worker + Frontend)
docker compose up --build
```


Espera a que veas en los logs:
- `localstack | Ready.` — LocalStack listo
- `backend | Uvicorn running on http://0.0.0.0:8000` — API lista
- `worker | Worker starting...` — Worker consumiendo


### Probar manualmente


```bash
# 1. Verificar que el API responde
curl http://localhost:8000/


# 2. Registrar un usuario
curl -X POST http://localhost:8000/auth/register \
 -H "Content-Type: application/json" \
 -d '{"username": "testuser", "password": "password123"}'


# 3. Hacer login y obtener token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
 -H "Content-Type: application/json" \
 -d '{"username": "testuser", "password": "password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")


echo "Token: $TOKEN"


# 4. Crear un job de reporte
curl -X POST http://localhost:8000/jobs \
 -H "Content-Type: application/json" \
 -H "Authorization: Bearer $TOKEN" \
 -d '{
   "report_type": "sales",
   "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
   "format": "csv"
 }'


# 5. Listar jobs (debería mostrar el job en PENDING o PROCESSING)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/jobs


# 6. Esperar 5-30 segundos y volver a listar (debería estar COMPLETED)
sleep 15
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/jobs


# 7. Health check
curl http://localhost:8000/health
```


### Probar el frontend


Abre http://localhost:3000 en el navegador:
1. Regístrate con un usuario
2. Haz login
3. Crea un reporte desde el formulario
4. Observa cómo el estado cambia automáticamente (PENDING → PROCESSING → COMPLETED)


### Correr tests del backend


```bash
# Instalar dependencias de test
cd backend
pip install -r requirements-test.txt


# Correr tests con cobertura
pytest tests/ -v --cov=app --cov-report=term-missing


# Volver al root
cd ..
```


### Detener todo


```bash
docker compose down
```


---


## 2. Preparar cuenta AWS


### 2.1 Instalar AWS CLI


```bash
# macOS
brew install awscli


# Verificar
aws --version
```


### 2.2 Crear un usuario IAM para ti (si no tienes uno)


1. Ve a la consola AWS → IAM → Users → Create user
2. Nombre: `tu-nombre-admin`
3. Attach policy: `AdministratorAccess`
4. Create access key → Command Line Interface
5. Guarda el Access Key ID y Secret Access Key


### 2.3 Configurar AWS CLI


```bash
aws configure
# AWS Access Key ID: <tu-access-key>
# AWS Secret Access Key: <tu-secret-key>
# Default region name: us-east-1
# Default output format: json
```


### 2.4 Crear un Key Pair para EC2


```bash
# Crear key pair y guardar la clave privada
aws ec2 create-key-pair \
 --key-name async-reports-key \
 --query 'KeyMaterial' \
 --output text > ~/.ssh/async-reports-key.pem


# Dar permisos correctos
chmod 400 ~/.ssh/async-reports-key.pem
```


---


## 3. Crear infraestructura con Terraform


### 3.1 Instalar Terraform


```bash
# macOS
brew install terraform


# Verificar
terraform --version
```


### 3.2 Inicializar y aplicar


```bash
cd infra/terraform


# Inicializar providers
terraform init


# Ver qué se va a crear (revisar que todo se vea bien)
terraform plan \
 -var="key_pair_name=async-reports-key" \
 -var="jwt_secret=$(openssl rand -hex 32)"


# Crear la infraestructura
terraform apply \
 -var="key_pair_name=async-reports-key" \
 -var="jwt_secret=$(openssl rand -hex 32)"


# Escribir "yes" cuando pregunte
```


### 3.3 Guardar los outputs


Terraform va a mostrar los outputs al final. Guárdalos:


```bash
# Ver outputs
terraform output


# Deberías ver algo como:
# ec2_public_ip = "54.123.45.67"
# public_url = "http://54.123.45.67"
# sqs_standard_queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/async-reports-reports-queue-standard"
# sqs_high_queue_url = "https://sqs.us-east-1.amazonaws.com/123456789/async-reports-reports-queue-high"
```


**Anota estos valores**, los necesitas para los GitHub Secrets.


### 3.4 Verificar que la instancia EC2 está corriendo


```bash
# SSH a la instancia (espera 2-3 minutos después del terraform apply para que el user_data termine)
ssh -i ~/.ssh/async-reports-key.pem ec2-user@<EC2_PUBLIC_IP>


# Verificar que Docker está instalado
docker --version
docker-compose --version


# Salir
exit
```


---


## 4. Subir a GitHub


### 4.1 Crear repositorio en GitHub


1. Ve a https://github.com/new
2. Nombre: `tu-nombre-prosperas-challenge`
3. Público
4. NO inicializar con README (ya tenemos uno)
5. Create repository


### 4.2 Inicializar git y subir


```bash
# Desde la raíz del proyecto
git init
git add .
git commit -m "feat: initial implementation of async report processing system"


# Conectar con GitHub
git remote add origin https://github.com/<TU-USUARIO>/tu-nombre-prosperas-challenge.git
git branch -M main
git push -u origin main
```


### 4.3 Actualizar el badge en README.md


Edita `README.md` y reemplaza `<OWNER>/<REPO>` con tu usuario y nombre de repo:


```markdown
[![Deploy to AWS](https://github.com/TU-USUARIO/tu-nombre-prosperas-challenge/actions/workflows/deploy.yml/badge.svg)](https://github.com/TU-USUARIO/tu-nombre-prosperas-challenge/actions/workflows/deploy.yml)
```


```bash
git add README.md
git commit -m "docs: update CI/CD badge URL"
git push
```


---


## 5. Configurar GitHub Secrets


Ve a tu repo en GitHub → Settings → Secrets and variables → Actions → New repository secret


Crea estos secretos uno por uno:


| Secret Name | Valor | De dónde sacarlo |
|-------------|-------|-------------------|
| `AWS_ACCESS_KEY_ID` | Tu access key de AWS | Paso 2.2 |
| `AWS_SECRET_ACCESS_KEY` | Tu secret key de AWS | Paso 2.2 |
| `EC2_HOST` | IP pública de la instancia EC2 | `terraform output ec2_public_ip` |
| `EC2_SSH_KEY` | Contenido completo del archivo .pem | `cat ~/.ssh/async-reports-key.pem` |
| `JWT_SECRET` | Un string aleatorio largo | `openssl rand -hex 32` |
| `REPO_URL` | URL HTTPS de tu repo | `https://github.com/TU-USUARIO/tu-nombre-prosperas-challenge.git` |
| `DYNAMODB_JOBS_TABLE` | Nombre de la tabla jobs | `terraform output` (ej: `async-reports-jobs`) |
| `DYNAMODB_USERS_TABLE` | Nombre de la tabla users | `terraform output` (ej: `async-reports-users`) |
| `SQS_STANDARD_QUEUE_URL` | URL completa de la cola estándar | `terraform output sqs_standard_queue_url` |
| `SQS_HIGH_QUEUE_URL` | URL completa de la cola high | `terraform output sqs_high_queue_url` |


**Para EC2_SSH_KEY**: copia TODO el contenido del archivo .pem, incluyendo las líneas `-----BEGIN RSA PRIVATE KEY-----` y `-----END RSA PRIVATE KEY-----`.


---


## 6. Primer despliegue


### Opción A: Trigger automático (push a main)


```bash
# Cualquier push a main dispara el pipeline
git commit --allow-empty -m "ci: trigger first deployment"
git push
```


Ve a GitHub → Actions para ver el progreso del pipeline.


### Opción B: Despliegue manual por SSH (si el pipeline falla la primera vez)


```bash
# SSH a la instancia
ssh -i ~/.ssh/async-reports-key.pem ec2-user@<EC2_PUBLIC_IP>


# Clonar el repo
cd /home/ec2-user/app
git clone https://github.com/TU-USUARIO/tu-nombre-prosperas-challenge.git .


# Crear archivo .env de producción
cat > .env << EOF
AWS_REGION=us-east-1
JWT_SECRET=<TU_JWT_SECRET>
JWT_EXPIRATION_MINUTES=60
DYNAMODB_JOBS_TABLE=<NOMBRE_TABLA_JOBS>
DYNAMODB_USERS_TABLE=<NOMBRE_TABLA_USERS>
SQS_STANDARD_QUEUE_URL=<URL_COLA_STANDARD>
SQS_HIGH_QUEUE_URL=<URL_COLA_HIGH>
WORKER_CONCURRENCY=2
WORKER_POLL_INTERVAL=1
WORKER_VISIBILITY_TIMEOUT=30
EOF


# Crear docker-compose de producción (sin LocalStack)
cat > docker-compose.prod.yml << 'EOF'
version: "3.8"
services:
 backend:
   build:
     context: ./backend
   ports:
     - "8000:8000"
   env_file: .env
   restart: always


 worker:
   build:
     context: ./worker
   env_file: .env
   restart: always


 frontend:
   build:
     context: ./frontend
   ports:
     - "80:80"
   depends_on:
     - backend
   restart: always
EOF


# Build y levantar
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d


# Verificar que los contenedores están corriendo
docker ps


# Ver logs
docker-compose -f docker-compose.prod.yml logs -f
```


---


## 7. Verificar que todo funciona


### 7.1 Desde tu máquina local


```bash
EC2_IP="<TU_EC2_PUBLIC_IP>"


# Health check
curl http://$EC2_IP/health


# Registrar usuario
curl -X POST http://$EC2_IP/auth/register \
 -H "Content-Type: application/json" \
 -d '{"username": "demo", "password": "demo12345"}'


# Login
TOKEN=$(curl -s -X POST http://$EC2_IP/auth/login \
 -H "Content-Type: application/json" \
 -d '{"username": "demo", "password": "demo12345"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")


# Crear job
curl -X POST http://$EC2_IP/jobs \
 -H "Content-Type: application/json" \
 -H "Authorization: Bearer $TOKEN" \
 -d '{
   "report_type": "sales",
   "date_range": {"start_date": "2024-01-01", "end_date": "2024-12-31"},
   "format": "pdf"
 }'


# Crear job de alta prioridad
curl -X POST http://$EC2_IP/jobs \
 -H "Content-Type: application/json" \
 -H "Authorization: Bearer $TOKEN" \
 -d '{
   "report_type": "analytics",
   "date_range": {"start_date": "2024-06-01", "end_date": "2024-06-30"},
   "format": "json",
   "priority": "high"
 }'


# Listar jobs
curl -H "Authorization: Bearer $TOKEN" http://$EC2_IP/jobs


# Esperar y verificar que se completan
sleep 30
curl -H "Authorization: Bearer $TOKEN" http://$EC2_IP/jobs
```


### 7.2 Desde el navegador


1. Abre `http://<EC2_PUBLIC_IP>` en el navegador
2. Regístrate y haz login
3. Crea varios reportes
4. Observa cómo cambian de estado automáticamente


### 7.3 Verificar en la consola AWS


1. **DynamoDB** → Tables → Verifica que las tablas `async-reports-jobs` y `async-reports-users` existen y tienen items
2. **SQS** → Queues → Verifica que las 4 colas existen (standard, high, 2 DLQs)
3. **EC2** → Instances → Verifica que la instancia t2.micro está running


---


## 8. Crear usuario IAM para revisión


Esto es lo que pide la prueba para que el evaluador pueda revisar tu infraestructura.


```bash
# Crear usuario IAM
aws iam create-user --user-name prosperas-reviewer


# Dar permisos de administrador
aws iam attach-user-policy \
 --user-name prosperas-reviewer \
 --policy-arn arn:aws:iam::aws:policy/AdministratorAccess


# Crear access keys
aws iam create-access-key --user-name prosperas-reviewer
```


**Guarda el Access Key ID y Secret Access Key** que devuelve el último comando. Estos son los que envías al evaluador.


---


## 9. Limpieza (después de la evaluación)


### Eliminar usuario IAM de revisión


```bash
# Listar y eliminar access keys
aws iam list-access-keys --user-name prosperas-reviewer
aws iam delete-access-key --user-name prosperas-reviewer --access-key-id <ACCESS_KEY_ID>


# Desattach policy
aws iam detach-user-policy \
 --user-name prosperas-reviewer \
 --policy-arn arn:aws:iam::aws:policy/AdministratorAccess


# Eliminar usuario
aws iam delete-user --user-name prosperas-reviewer
```


### Destruir infraestructura (para no generar costos)


```bash
# Primero detener los contenedores en EC2
ssh -i ~/.ssh/async-reports-key.pem ec2-user@<EC2_IP> "docker-compose -f docker-compose.prod.yml down"


# Destruir todo con Terraform
cd infra/terraform
terraform destroy \
 -var="key_pair_name=async-reports-key" \
 -var="jwt_secret=dummy"


# Eliminar key pair
aws ec2 delete-key-pair --key-name async-reports-key
rm ~/.ssh/async-reports-key.pem
```


---


## Checklist de Entrega


Antes de enviar, verifica:


- [ ] `docker compose up` funciona localmente sin errores
- [ ] Tests pasan con `pytest tests/ -v` (76%+ cobertura)
- [ ] La app está corriendo en `http://<EC2_IP>` y es accesible
- [ ] El pipeline de GitHub Actions tiene al menos una ejecución exitosa (badge verde)
- [ ] El README tiene el badge de CI/CD y la URL de producción
- [ ] Existen los archivos: TECHNICAL_DOCS.md, SKILL.md, AI_WORKFLOW.md
- [ ] No hay credenciales hardcodeadas en el código (buscar con `grep -r "AKIA" .`)
- [ ] El usuario IAM de revisión está creado
- [ ] El .env.example tiene todas las variables documentadas


## Datos para el email de entrega


```
Asunto: [Prosperas] Prueba Técnica — Tu Nombre


Contenido:
- Repositorio: https://github.com/TU-USUARIO/tu-nombre-prosperas-challenge
- URL de producción: http://<EC2_PUBLIC_IP>
- Credenciales IAM de revisión:
 - Access Key ID: <del paso 8>
 - Secret Access Key: <del paso 8>
 - Región: us-east-1
```



