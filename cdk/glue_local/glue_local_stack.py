import boto3
import json

# Configuración del cliente de AWS
s3 = boto3.client("s3")
sqs = boto3.client("sqs")

# Buckets y colas
bucket_audio = "my-audio-bucket"
queue_name = "s3-audio-processing-queue"

def setup_resources():
    try:
        # Crear bucket S3
        s3.create_bucket(Bucket=bucket_audio)
        print(f"[INFO] Bucket '{bucket_audio}' configurado.")

        # Crear cola SQS
        response = sqs.create_queue(QueueName=queue_name)
        queue_url = response["QueueUrl"]
        print(f"[INFO] Cola SQS '{queue_name}' configurada en URL: {queue_url}")

        # Configuración adicional como permisos (opcional)
        # Por ejemplo, suscripción SNS o políticas para acceso S3

    except Exception as e:
        print(f"[ERROR] Fallo en la configuración de recursos: {e}")

# Lógica principal
if __name__ == "__main__":
    setup_resources()
