# 📦 Laboratorio simulado de AWS para el proyecto de InnovatechFP

Este proyecto simula una arquitectura mínima de AWS en tu **entorno local** usando:
- LocalStack (servicios AWS en Docker)
- AWS CDK (infraestructura como código)
- Lambda en Python
- S3 como almacenamiento
- Makefile para automatizar todo
- AWS Glue para transformar los datos

---

## ✅ Servicios utilizados y su propósito

| Servicio AWS Simulado | Uso en el Proyecto |
|------------------------|---------------------|
| **S3**                | Almacena archivos subidos por la Lambda |
| **Lambda**            | Recibe un payload, crea un archivo y lo guarda en S3 |
| **IAM**               | Permite a la Lambda subir a S3 (grant_put) |
| **SSM**               | Necesario para el `cdk bootstrap` |
| **CloudFormation**    | CDK lo usa para desplegar stacks |
| **Glue**              | Transforma los datos|
| **SQS**               | Gestiona mensajes entre componentes del sistema|

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
source .venv/bin/activate
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
### 5. Abrir el servidor local donde se genera el audio
```bash
make audio-generator
```
Accede en tu navegador a http://localhost:8080

### 6. Simulación ETL
Abre una nueva terminal
```bash
make simulate
```

### 7. Probar que todo funciona
```bash
make list-bucket    # Verifica que el archivo esté en el bucket antes de procesarlos
make list-output-bucket    # Verifica que el archivo esté en el bucket final

```

---

## 🧪 Resultado esperado

```bash
$ make simulate


Esperando mensajes en la cola SQS...

Audio recibido: audio_1743405017434.webm

Descargando archivo audio_1743405017434.webm a /tmp/tmpg1nrvxqz.webm

Convirtiendo /tmp/tmpg1nrvxqz.webm a /tmp/tmp8pl3klqp.wav (WAV)

Reducción de ruido completada.

Subiendo /tmp/tmp0a8sny8j.wav a s3://my-audio-output-bucket/audio_1743405017434_processed.wav

Archivos temporales eliminados.

Audio audio_1743405017434.webm procesado y eliminado de cola
 ```


## 🧑‍💻 Autores

**Martín Amor**  
**Noelia Sánchez**  
**Inés Poses**  
**Celia Incera**   
💻 2025 — Laboratorio simulado para el proyecto de InnovatechFP
