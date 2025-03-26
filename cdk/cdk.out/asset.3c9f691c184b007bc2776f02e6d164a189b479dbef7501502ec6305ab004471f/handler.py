import boto3
import os
import json
import traceback
import NoCredentialsError
import EndpointConnectionError
def main(event, context):
    print('entro')
    try:
        # s3 = boto3.client("s3", endpoint_url="http://localhost:4566")
        endpoint_url = os.environ.get("LOCALSTACK_ENDPOINT", "http://localhost:4566")
        s3 = boto3.client("s3", endpoint_url=endpoint_url)
        bucket = os.environ["BUCKET_NAME"]

        print("[INFO] Payload recibido:", event)

        # Parsear JSON del evento
        if isinstance(event, str):
            body = json.loads(event)
        else:
            body = event

        filename = body.get("filename", "archivo.txt")
        content = body.get("content", "Contenido por defecto")

        tmp_path = f"/tmp/{filename}"
        with open(tmp_path, "w") as f:
            print('Opening file')
            f.write(content)

        print(f"[INFO] Subiendo {filename} a {bucket} desde {tmp_path}")
        try:
            s3.upload_file(tmp_path, bucket, filename)
        except NoCredentialsError:
            print("[ERROR] No se proporcionaron credenciales para S3.")
        except EndpointConnectionError as e:
            print(f"[ERROR] No se pudo conectar al endpoint: {endpoint_url}. Error: {e}")
        except Exception as e:
            print(f"[ERROR] Error inesperado: {e}")

        return {
            "statusCode": 200,
            "body": json.dumps(f"{filename} subido correctamente a {bucket}")
        }

    except Exception as e:
        print("[ERROR]", str(e))
        traceback.print_exc()
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }