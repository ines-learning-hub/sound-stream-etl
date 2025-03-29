import boto3
import botocore
import noisereduce as nr
import soundfile as sf
import io
from scipy.io import wavfile
import time
import os
import re
import json
from dotenv import load_dotenv
import ffmpeg
from cdk.lambda_s3_local.lambda_code.s3_uploader import S3Uploader

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
def advanced_noise_reduction_in_memory(audio_data):
    # Cargar el audio desde el objeto de memoria
    try:
        audio_data.seek(0)  # Asegúrate de que el puntero esté al inicio
        data, rate = sf.read(audio_data, dtype='int16')
    except Exception as e:
        print(f"[ERROR] Fallo al leer el archivo con soundfile: {e}")
        return
    # Realizar la reducción de ruido
    reduced_noise = nr.reduce_noise(y=data, sr=rate)

    # Guardar el audio reducido en un objeto de memoria
    output_audio = io.BytesIO()
    sf.write(output_audio, reduced_noise, rate, format="wav")
    output_audio.seek(0)  # Resetear el cursor del archivo
    print("Reducción de ruido completada")
    return audio_data

# Flujo ETL: Descarga, procesado y subida
def process_audio_file(audio_file):
    # Asegurarse que los buckets existen
    ensure_bucket_exists(bucket_audio)
    ensure_bucket_exists(bucket_audio_out)

    # print(f"Leyendo {audio_file} desde s3://{bucket_audio}/...")
    try:
        response = s3.get_object(Bucket=bucket_audio, Key=audio_file)
        audio_data = io.BytesIO(response['Body'].read())
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print(f"El archivo {audio_file} no existe en el bucket {bucket_audio}.")
        else:
            print(f"Error al descargar el archivo: {e.response['Error']['Message']}")
        return

    try:
        converted_audio = io.BytesIO()
        process = (
            ffmpeg
            .input("pipe:0", format="webm")  # Entrada estándar
            .output("pipe:1", format="wav")  # Salida estándar
            .run(input=audio_data.getvalue(), capture_stdout=True, capture_stderr=True)
        )
        converted_audio.write(process[0])
        converted_audio.seek(0)
        print("Conversión a WAV completada.")
    except ffmpeg.Error as e:
        print(f"[ERROR] Error durante la conversión a WAV: {e}")
        print("[ERROR] Detalles de stderr:", e.stderr.decode("utf-8"))
        return

        # Reducir ruido en el archivo convertido
    print("Aplicando reducción de ruido...")
    processed_audio = advanced_noise_reduction_in_memory(converted_audio)

    # Subir el archivo procesado al bucket de salida
    output_key = f"{audio_file.split('.')[0]}.wav"
    # print(f"Procesando reducción de ruido para {audio_file}...")
    #processed_audio = advanced_noise_reduction_in_memory(audio_data)

    # print(f"Subiendo {output_key} a s3://{bucket_audio_out}/...")
    s3.put_object(
        Bucket=bucket_audio_out,
        Key=output_key,
        Body=processed_audio
    )
    # print(f"Archivo procesado subido correctamente a s3://{bucket_audio_out}/{output_key}")


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

#sqs = boto3.client("sqs",  endpoint_url="http://"+os.getenv("IP_ADDRESS")+":4566")
#setup_sqs('s3-queue')
#poll_sqs_messages(sqs, "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/s3-queue")
process_audio_file('engine-6000.webm')