import boto3
import botocore
from datetime import datetime


s3 = boto3.client("s3", endpoint_url="http://172.26.178.148:4566")

bucket_in = "my-local-bucket"
bucket_out = "my-glue-output-bucket"
input_key = "archivo.txt"

#Verifica que el bucket de salida existe
def ensure_bucket_exists(bucket_name):
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"Bucket {bucket_name} ya existe")
    except botocore.exceptions.ClientError:
        print(f"Creando bucket {bucket_name}")
        s3.create_bucket(Bucket=bucket_name)


#Crear bucket si no existe
ensure_bucket_exists(bucket_out)

#Leer archivo de entrada
print(f"Leyendo {input_key} desde s3://{bucket_in}/...")
response = s3.get_object(Bucket=bucket_in, Key=input_key)
content = response['Body'].read().decode('utf-8').strip()

#Obtener fecha actual
now = datetime.now()
year, month, day = now.year, f"{now.month:02}", f"{now.day:02}"
output_key = f"output/year={year}/month={month}/day={day}/ejemplo.csv"

#Subir archivo procesado
print(f"Escribiendo archivo en s3://{bucket_out}/{output_key} ...")
s3.put_object(
    Bucket=bucket_out,
    Key=output_key,
    Body=content.encode('utf-8'),
    ContentType='text/csv'
)

print("Proceso completado. Archivo particionado guardado correctamente")
