import boto3
import os
import time
import traceback

class S3Uploader:
    def __init__(self):
        self.bucket_name = os.environ["BUCKET_NAME"]
        self.endpoint_url = os.environ.get("LOCALSTACK_ENDPOINT", "http://localhost:4566")
        self.s3_client = boto3.client("s3", endpoint_url=self.endpoint_url)

    def handle_request(self, event):
        try:
            if 'body' not in event or not event['body']:
                return {
                    "statusCode": 400,
                    "body": "No se proporcionó ningún archivo en la solicitud."
                }

             # Validar el tipo de contenido
            content_type = event['headers'].get('Content-Type', '')
            if content_type != 'application/octet-stream':
                return {
                    "statusCode": 400,
                    "body": "Tipo de contenido inválido. Se espera 'application/octet-stream'."
                }

            # Extraer los datos binarios del archivo y generar un nombre único
            file_data = event['body']  # Datos binarios del archivo enviado
            file_name = self.generate_filename(event)

            self.upload_to_s3(file_data, file_name)
            self.notify_glue(file_name)
            return {
                "statusCode": 200,
                "body": f"Archivo subido correctamente como {file_name}."
            }
        except Exception as e:
            print("[ERROR]", str(e))
            traceback.print_exc()
            return {
                "statusCode": 500,
                "body": f"Error al procesar la solicitud: {str(e)}"
            }

    def generate_filename(self, event):
        timestamp = int(time.time() * 1000)  
        return f"audio_{timestamp}.webm"

    def upload_to_s3(self, file_data, file_name):
        try:
            print(f"[INFO] Subiendo {file_name} a {self.bucket_name}")
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=file_data
            )
        except Exception as e:
            raise RuntimeError(f"Error subiendo archivo a S3: {e}")

    def notify_glue(self, file_name):
        try:
            # Configuración del cliente SNS
            sns = boto3.client("sns", endpoint_url="http://172.31.205.25:4566")  # Reemplaza con la IP correcta si es necesario
            topic_arn = "arn:aws:sns:us-east-1:000000000000:my-local-topic"  # Reemplaza con tu ARN
            
            # Publicar mensaje al tema SNS
            response = sns.publish(
                TopicArn=topic_arn,
                Message=f'{{"bucket_name": "my-local-bucket", "key_name": "{file_name}"}}',
            )
            
            print(f"Notificación enviada exitosamente: {response}")
        except Exception as e:
            print(f"[ERROR] Falló la publicación al tema SNS: {e}")
      
    def _response(self, status_code, message):
        return {
            "statusCode": status_code,
            "headers": {
                "Access-Control-Allow-Origin": "*",  # ⬅️ Permite acceso desde cualquier origen
                "Access-Control-Allow-Methods": "OPTIONS, POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": message
        }


