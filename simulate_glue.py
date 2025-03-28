import boto3
import botocore
import noisereduce as nr
import soundfile as sf
import io
from scipy.io import wavfile

# Cliente S3 con LocalStack
s3 = boto3.client("s3", endpoint_url="http://172.26.178.148:4566")

# Buckets y claves
bucket_audio = "my-audio-bucket"
bucket_audio_out = "my-audio-output-bucket"
input_key_audio = "engine-6000.wav"  # Esto es una prueba

# Verifica si el bucket existe, y si no, lo crea
def ensure_bucket_exists(bucket_name):
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"Bucket {bucket_name} ya existe")
    except botocore.exceptions.ClientError:
        print(f"Creando bucket {bucket_name}")
        s3.create_bucket(Bucket=bucket_name)

# Función para reducción de ruido en memoria
def advanced_noise_reduction_in_memory(audio_data):
    # Cargar el audio desde el objeto de memoria
    rate, data = wavfile.read(audio_data)

    # Realizar la reducción de ruido
    reduced_noise = nr.reduce_noise(y=data, sr=rate)

    # Guardar el audio reducido en un objeto de memoria
    output_audio = io.BytesIO()
    sf.write(output_audio, reduced_noise, rate, format="wav")
    output_audio.seek(0)  # Resetear el cursor del archivo
    return output_audio

# Flujo ETL: Descarga, procesado y subida
def process_audio_file():
    # Asegurarse que los buckets existen
    ensure_bucket_exists(bucket_audio)
    ensure_bucket_exists(bucket_audio_out)

    # Descargar el archivo de entrada desde S3 directamente a memoria
    print(f"Leyendo {input_key_audio} desde s3://{bucket_audio}/...")
    try:
        response = s3.get_object(Bucket=bucket_audio, Key=input_key_audio)
        audio_data = io.BytesIO(response['Body'].read())
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print(f"El archivo {input_key_audio} no existe en el bucket {bucket_audio}.")
        else:
            print(f"Error al descargar el archivo: {e.response['Error']['Message']}")
        return

    # Reducir ruido en el archivo descargado (en memoria)
    print(f"Procesando reducción de ruido para {input_key_audio}...")
    processed_audio = advanced_noise_reduction_in_memory(audio_data)

    # Subir el archivo procesado al bucket de salida
    output_key = f"{input_key_audio}"
    print(f"Subiendo {output_key} a s3://{bucket_audio_out}/...")
    s3.put_object(
        Bucket=bucket_audio_out,
        Key=output_key,
        Body=processed_audio,
        ContentType="audio/wav"
    )
    print(f"Archivo procesado subido correctamente a s3://{bucket_audio_out}/{output_key}")

# Ejecutar el flujo ETL
process_audio_file()
