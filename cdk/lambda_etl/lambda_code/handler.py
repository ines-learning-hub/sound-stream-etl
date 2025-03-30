import json
import sys
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
import boto3
import json
import io
import ffmpeg
import noisereduce as nr
import soundfile as sf

# Inicializar Glue y Spark
sc = SparkContext()
glueContext = GlueContext(sc)

# Argumentos pasados al trabajo
args = getResolvedOptions(sys.argv, ['INPUT_BUCKET', 'OUTPUT_BUCKET', 'QUEUE_URL'])
input_bucket = args['INPUT_BUCKET']
output_bucket = args['OUTPUT_BUCKET']
queue_url = args['QUEUE_URL']

# Cliente S3
s3 = boto3.client("s3")

# Función para reducir ruido del audio
def advanced_noise_reduction_in_memory(audio_data):
    try:
        audio_data.seek(0)
        data, rate = sf.read(audio_data, dtype='int16')
    except Exception as e:
        print(f"[ERROR] Fallo al leer el archivo: {e}")
        return
    reduced_noise = nr.reduce_noise(y=data, sr=rate)
    output_audio = io.BytesIO()
    sf.write(output_audio, reduced_noise, rate, format="wav")
    output_audio.seek(0)
    return output_audio

# Procesar archivo desde S3
def process_audio_file(file_name):
    try:
        # Descargar archivo desde S3
        response = s3.get_object(Bucket=input_bucket, Key=file_name)
        audio_data = io.BytesIO(response["Body"].read())
        print(f"[INFO] Archivo descargado: {file_name}")

        # Convertir a WAV
        converted_audio = io.BytesIO()
        process = (
            ffmpeg
            .input("pipe:0", format="webm")
            .output("pipe:1", format="wav")
            .run(input=audio_data.getvalue(), capture_stdout=True, capture_stderr=True)
        )
        converted_audio.write(process[0])
        converted_audio.seek(0)

        # Aplicar reducción de ruido
        processed_audio = advanced_noise_reduction_in_memory(converted_audio)

        # Subir archivo transformado a S3
        output_key = f"{file_name.split('.')[0]}.wav"
        s3.put_object(Bucket=output_bucket, Key=output_key, Body=processed_audio)
        print(f"[INFO] Archivo procesado y guardado: {output_bucket}/{output_key}")
    except Exception as e:
        print(f"[ERROR] Fallo en el procesamiento: {e}")

def main(event, context):
    for message in event['Records']:
        print('message', message.keys())
        body=json.loads(message['body'])
  
        # print("tipo mensaje", type(message))
        data=json.loads(body['Message'])
        print(data)

        print(f"Audio recibido desde lambda: {data['file_name']}")
        process_audio_file(data['file_name'])
