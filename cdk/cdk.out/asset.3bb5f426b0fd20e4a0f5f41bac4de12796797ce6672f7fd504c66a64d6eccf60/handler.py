import boto3
import os
import json

def main(event, context):
    s3 = boto3.client("s3", endpoint_url="http://localhost:4566")
    bucket = os.environ["BUCKET_NAME"]

    # Parsear payload
    body = json.loads(event) if isinstance(event, str) else event
    filename = body.get("filename", "archivo.txt")
    content = body.get("content", "Contenido por defecto")

    # Guardar temporalmente
    file_path = f"/tmp/{filename}"
    with open(file_path, "w") as f:
        f.write(content)

    # Subir a S3
    s3.upload_file(file_path, bucket, filename)

    return {
        "statusCode": 200,
        "body": json.dumps(f"Archivo '{filename}' subido a bucket {bucket}")
    }