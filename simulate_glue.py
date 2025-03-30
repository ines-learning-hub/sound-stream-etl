import boto3
import botocore
import noisereduce as nr
import soundfile as sf
import os
import ffmpeg
import tempfile
from dotenv import load_dotenv
import time, json

load_dotenv()
endpoint="http://"+os.getenv("IP_ADDRESS")+":4566"
# Cliente S3 con LocalStack
s3 = boto3.client("s3", endpoint_url=endpoint)

# Buckets y claves
bucket_audio = "my-audio-bucket"
bucket_audio_out = "my-audio-output-bucket"

# Verifica si el bucket existe, y si no, lo crea
def ensure_bucket_exists(bucket_name):
    try:
        s3.head_bucket(Bucket=bucket_name)
        # print(f"Bucket {bucket_name} ya existe")
    except botocore.exceptions.ClientError:
        print(f"Creando bucket {bucket_name}")
        # s3.create_bucket(Bucket=bucket_name)

# Función para reducción de ruido en memoria
def advanced_noise_reduction_in_file(input_path, output_path):
    try:
        with sf.SoundFile(input_path) as file:
            data = file.read(dtype='int16')
            rate = file.samplerate
        reduced_noise = nr.reduce_noise(y=data, sr=rate)
        sf.write(output_path, reduced_noise, rate, format="wav")
        print("Reducción de ruido completada.")
    except Exception as e:
        print(f"[ERROR] Fallo durante la reducción de ruido: {e}")


# Flujo ETL: Descarga, procesado y subida
def process_audio_file(audio_file):
    ensure_bucket_exists(bucket_audio)
    ensure_bucket_exists(bucket_audio_out)

    try:
        # Descargar el archivo a un archivo temporal local
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_input_file:
            print(f"Descargando archivo {audio_file} a {temp_input_file.name}")
            s3.download_fileobj(bucket_audio, audio_file, temp_input_file)
            temp_input_path = temp_input_file.name
    except botocore.exceptions.ClientError as e:
        print(f"Error al descargar el archivo: {e.response['Error']['Message']}")
        return

    try:
        # Convertir el archivo .webm a .wav
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_output_file:
            temp_output_path = temp_output_file.name
            print(f"Convirtiendo {temp_input_path} a {temp_output_path} (WAV)")
            (
                ffmpeg
                .input(temp_input_path)
                .output(temp_output_path, format="wav", ac=1, ar="16000")  # Monocanal, 16 kHz
                .run(quiet=True, overwrite_output=True)
            )
    except ffmpeg.Error as e:
        print(f"[ERROR] Error durante la conversión a WAV: {e}")
        return

    try:
        # Aplicar reducción de ruido
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_reduced_file:
            reduced_path = temp_reduced_file.name
            advanced_noise_reduction_in_file(temp_output_path, reduced_path)
    except Exception as e:
        print(f"[ERROR] Fallo al procesar el archivo: {e}")
        return

    try:
        # Subir el archivo procesado al bucket de salida
        output_key = f"{os.path.splitext(audio_file)[0]}_processed.wav"
        print(f"Subiendo {reduced_path} a s3://{bucket_audio_out}/{output_key}")
        with open(reduced_path, "rb") as file:
            s3.upload_fileobj(file, bucket_audio_out, output_key)
    except Exception as e:
        print(f"[ERROR] Fallo al subir el archivo procesado: {e}")
    finally:
        # Limpiar archivos temporales
        os.remove(temp_input_path)
        os.remove(temp_output_path)
        os.remove(reduced_path)
        print("Archivos temporales eliminados.")


def setup_sqs(queue_name):

    try:
        sns = boto3.client("sns",  endpoint_url="http://"+os.getenv("IP_ADDRESS")+":4566")
        topics = sns.list_topics()
        topic_arn = topics['Topics'][0]['TopicArn']

        response = sqs.create_queue(QueueName=queue_name)
        queue_url = response["QueueUrl"]
        print(f"[INFO] Queue URL: {queue_url}")

        # Obtener el ARN de la cola
        attributes = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=["QueueArn"]
        )
        queue_arn = attributes["Attributes"]["QueueArn"]

        # Configurar política de permisos para el topic SNS
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "sqs:SendMessage",
                    "Resource": queue_arn,
                    "Condition": {
                        "ArnEquals": {
                            "aws:SourceArn": topic_arn
                        }
                    }
                }
            ]
        }
        sqs.set_queue_attributes(
            QueueUrl=queue_url,
            Attributes={"Policy": str(policy)}
        )
        print("[INFO] Configuración de permisos para SQS completada")

        sns.subscribe(
            TopicArn=topic_arn,
            Protocol="sqs",
            Endpoint=queue_arn
        )
        print(f"[INFO] Cola SQS {queue_arn} suscrita al Topic SNS {topic_arn}")
        return sqs
    except Exception as e:
        print("[ERROR] Falló la configuración de la cola SQS:", str(e))

def poll_sqs_messages(sqs, queue_url):
    print("Esperando mensajes en la cola SQS...")
    while True:
        response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
        if "Messages" in response:
            for message in response["Messages"]:
                body=json.loads(message['Body'])
                data=json.loads(body['Message'])
                print(f"Audio recibido: {data['file_name']}")

                process_audio_file(data['file_name'])

                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
                print(f"Audio {data['file_name']} procesado y eliminado de cola")
                print()
        time.sleep(5)

sqs = boto3.client("sqs",  endpoint_url="http://"+os.getenv("IP_ADDRESS")+":4566")
setup_sqs('s3-queue')
poll_sqs_messages(sqs, "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/s3-queue")
#process_audio_file('engine-6000.webm')