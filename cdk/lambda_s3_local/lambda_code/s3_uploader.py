import boto3
import os
import json
import traceback

class S3Uploader:
    def __init__(self):
        self.bucket_name = os.environ["BUCKET_NAME"]
        self.endpoint_url = os.environ.get("LOCALSTACK_ENDPOINT", "http://localhost:4566")
        self.s3_client = boto3.client("s3", endpoint_url=self.endpoint_url)

    def process_event(self, event):
        try:
            if isinstance(event, str):
                body = json.loads(event)
            else:
                body = event
            
            # Extraer datos del JSON de audio
            timestamp = body.get("timestamp", "unknown")
            audio_data = body.get("audioData", {})

            # Usar el timestamp como nombre de archivo
            filename = f"audio_{timestamp}.json"
            content = json.dumps(audio_data)  # Convertir el contenido a string JSON

            #filename = body.get("filename", "archivo.txt")
            #content = body.get("content", "Contenido por defecto")
            return filename, content
        except Exception as e:
            raise ValueError(f"Error procesando el evento: {e}")

    def create_temp_file(self, filename, content):
        tmp_path = f"/tmp/{filename}"
        try:
            with open(tmp_path, "w") as f:
                print('Opening file')
                f.write(content)
            return tmp_path
        except Exception as e:
            raise IOError(f"Error creando archivo temporal: {e}")

    def upload_file(self, file_path, filename):
        try:
            print(f"[INFO] Subiendo {filename} a {self.bucket_name} desde {file_path}")
            self.s3_client.upload_file(file_path, self.bucket_name, filename)
        except Exception as e:
            raise RuntimeError(f"Error subiendo archivo a S3: {e}")

    def handle_request(self, event):
        try:
            filename, content = self.process_event(event)
            file_path = self.create_temp_file(filename, content)
            self.upload_file(file_path, filename)
            return {
                "statusCode": 200,
                "body": json.dumps(f"{filename} subido correctamente a {self.bucket_name}.")
            }
        except Exception as e:
            print("[ERROR]", str(e))
            traceback.print_exc()
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }


