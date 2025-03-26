# 📦 Proyecto: Lambda + S3 en Local con AWS Simulado

Este proyecto simula una arquitectura mínima de AWS en tu **entorno local** usando:
- LocalStack (servicios AWS en Docker)
- AWS CDK (infraestructura como código)
- Lambda en Python
- S3 como almacenamiento
- Makefile para automatizar todo

✅ Ideal para aprender AWS sin gastar 💸, validar arquitecturas, hacer pruebas de microservicios o enseñar DevOps con bajo consumo de recursos.

---

## ✅ Servicios utilizados y su propósito

| Servicio AWS Simulado | Uso en el Proyecto |
|------------------------|---------------------|
| **S3**                | Almacena archivos subidos por la Lambda |
| **Lambda**            | Recibe un payload, crea un archivo y lo guarda en S3 |
| **IAM**               | Permite a la Lambda subir a S3 (grant_put) |
| **SSM**               | Necesario para el `cdk bootstrap` |
| **CloudFormation**    | CDK lo usa para desplegar stacks |

---

## 📁 Estructura del proyecto

```
personal_local_aws/
├── docker-compose.yml           # Configuración de LocalStack
├── Makefile                     # Tareas automatizadas (deploy, invoke, etc)
├── response.json                # Output de la Lambda
├── cdk/
│   ├── app.py                   # Entry point de CDK
│   ├── cdk.json                 # Configuración para CDK local
│   ├── requirements.txt         # Dependencias CDK
│   └── lambda_s3_local/
│       ├── lambda_code/
│       │   └── handler.py       # Código Lambda
│       └── lambda_s3_local_stack.py  # Define Lambda + S3
```

---

## 🛠️ Requisitos previos

Asegúrate de tener lo siguiente instalado:

- Python 3.9+
- Docker + Docker Compose
- Node.js >= 18.x (¡Evita v23 por warning de JSII!)
- `awscli` y `awscli-local`:
  ```bash
  pip3 install awscli awscli-local
  ```
- `cdklocal` (CLI local de CDK):
  ```bash
  npm install -g aws-cdk-local aws-cdk
  ```

---

## ⚙️ Instalación paso a paso

### 1. Instalar dependencias CDK

```bash
cd cdk
python3 -m venv .venv
pip3 install -r requirements.txt
```

### 2. Iniciar LocalStack

```bash
make start-localstack
```

### 3. Bootstrap del entorno local (solo 1 vez)

```bash
make bootstrap
```

### 4. Desplegar Lambda + S3

```bash
make deploy
```

### 5. Probar que todo funciona

```bash
make invoke         # Ejecuta la Lambda y sube archivo a S3
make list-bucket    # Verifica que el archivo esté en el bucket
make get-object     # Descarga el archivo y muestra su contenido
```

---

## 🧪 Resultado esperado

```bash
$ make invoke
{
  "statusCode": 200,
  "body": ""archivo.txt subido correctamente a my-local-bucket""
}

$ make list-bucket
2025-03-23 22:35:01        15 archivo.txt

$ make get-object
Desde Makefile!
```

---

## 🧰 Makefile incluido

```makefile
start-localstack:
	docker-compose up -d

stop-localstack:
	docker-compose down

bootstrap:
	cd cdk && cdklocal bootstrap --app "python3 app.py"

deploy:
	cd cdk && cdklocal deploy LambdaS3LocalStack --require-approval never --app "python3 app.py"

invoke:
	awslocal lambda invoke \
		--function-name SaveToS3Function \
		--payload '{ "filename": "archivo.txt", "content": "Desde Makefile!" }' \
		response.json && cat response.json

list-bucket:
	awslocal s3 ls s3://my-local-bucket

get-object:
	awslocal s3 cp s3://my-local-bucket/archivo.txt -
```

---

## 🧠 Tips técnicos

- `host.docker.internal` se usa en `handler.py` para que la Lambda acceda a LocalStack desde su contenedor.
- Puedes revisar logs de la Lambda con:
  ```bash
  awslocal logs tail /aws/lambda/SaveToS3Function --follow
  ```
- El `cdk.json` incluye `"requireApproval": "never"` para despliegues automatizados.
- Todos los recursos tienen nombres explícitos (`SaveToS3Function`, `my-local-bucket`), ideal para testing.


Este paso es obligatorio para inicializar el entorno CDK.  
Debe ejecutarse desde dentro del folder `cdk/` porque ahí está el `app.py` y la configuración del proyecto:

```bash
cd cdk
cdklocal bootstrap --app "python3 app.py"
```
O usando el Makefile:

```bash
make bootstrap
```
Esto crea el stack CDKToolkit simulado, necesario para que el despliegue funcione.


`¿Por qué se ejecuta cdklocal bootstrap --app "python3 app.py"?` 

🧠 ¿Qué hace cdk bootstrap?

El comando bootstrap prepara el entorno para que AWS CDK (incluso usando LocalStack) pueda desplegar stacks correctamente.

Crea recursos iniciales obligatorios como:
- El stack CDKToolkit
- Parámetros en SSM Parameter Store
- Permisos, buckets y roles base (simulados por LocalStack)

📌 ¿Por qué debe ejecutarse dentro del folder cdk/?

Porque:
- El archivo cdk.json y app.py están dentro de cdk/
- cdklocal necesita ejecutar el app definido ahí
- Si lo ejecutas desde fuera, no encontrará app.py

📅 ¿Cuándo debes ejecutar el bootstrap?

✅ Solo la primera vez que vas a usar CDK Local con un nuevo stack o si hiciste make destroy.

---

## 📚 Extensiones posibles

- Agregar API Gateway local
- Usar DynamoDB Local
- Simular errores y retries
- Incorporar pruebas automatizadas en CI/CD offline

---

## 🧑‍💻 Autor

**Napoleon Lazardi**  
💻 2025 — Laboratorio educativo de AWS simulado

> ¡Aprende, desarrolla y automatiza sin pagar una sola línea en la nube! 🚀