import boto3
import os
import json
import traceback

def main(event, context):
    try:
        s3 = boto3.client("s3", endpoint_url="http://localhost:4566")
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
            f.write(content)

        print(f"[INFO] Subiendo {filename} a {bucket} desde {tmp_path}")
        s3.upload_file(tmp_path, bucket, filename)

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