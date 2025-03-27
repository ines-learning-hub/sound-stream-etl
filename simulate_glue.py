import boto3
import botocore
from datetime import datetime
import noisereduce as nr
import librosa
import os
from scipy.io import wavfile
import soundfile as sf

# Cliente S3 con LocalStack
s3 = boto3.client("s3", endpoint_url="http://172.26.178.148:4566")

# Buckets y claves
bucket_audio = "my-audio-bucket"  # Cambiado a un nombre válido
bucket_audio_out = "my-audio-output-bucket"
input_key_audio = "engine-6000.wav"

# Verifica si el bucket existe, y si no, lo crea
def ensure_bucket_exists(bucket_name):
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"Bucket {bucket_name} ya existe")
    except botocore.exceptions.ClientError:
        print(f"Creando bucket {bucket_name}")
        s3.create_bucket(Bucket=bucket_name)

# Función para reducción de ruido
def advanced_noise_reduction(input_path, output_path):
    # Load the audio file
    rate, data = wavfile.read(input_path)

    # Reduce the noise
    reduced_noise = nr.reduce_noise(y=data, sr=rate)

    # Save the noise-reduced audio file
    sf.write(output_path, reduced_noise, rate)
    print(f"Audio con reducción avanzada de ruido guardado en: {output_path}")

# Flujo ETL: Descarga, procesado y subida
def process_audio_file():
    # Asegurarse que los buckets existen
    ensure_bucket_exists(bucket_audio)
    ensure_bucket_exists(bucket_audio_out)

    # Descargar el archivo de entrada desde S3
    local_input_path = input_key_audio  # Se guardará localmente con el mismo nombre
    print(f"Leyendo {input_key_audio} desde s3://{bucket_audio}/...")
    try:
        response = s3.get_object(Bucket=bucket_audio, Key=input_key_audio)
        with open(local_input_path, "wb") as f:
            f.write(response['Body'].read())
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print(f"El archivo {input_key_audio} no existe en el bucket {bucket_audio}.")
        else:
            print(f"Error al descargar el archivo: {e.response['Error']['Message']}")
        return

    # Reducir ruido en el archivo descargado
    local_output_path = f"processed_{input_key_audio}"
    advanced_noise_reduction(local_input_path, local_output_path)

    # Subir el archivo procesado al bucket de salida
    print(f"Subiendo {local_output_path} a s3://{bucket_audio_out}/...")
    with open(local_output_path, "rb") as f:
        s3.put_object(
            Bucket=bucket_audio_out,
            Key=f"processed/{local_output_path}",
            Body=f,
            ContentType="audio/wav"
        )
    print(f"Archivo procesado subido correctamente a s3://{bucket_audio_out}/processed/{local_output_path}")

    # Limpieza de archivos locales
    os.remove(local_input_path)
    os.remove(local_output_path)

# Ejecutar el flujo ETL
process_audio_file()
