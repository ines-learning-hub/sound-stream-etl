import subprocess
import os
import json

def main(event, context):
    print("Evento recibido:", event)

    for record in event['Records']:
        try:
            # Leer el mensaje del SNS
            sns_message = json.loads(record['Sns']['Message'])
            bucket_name = sns_message.get("bucket_name")
            key_name = sns_message.get("key_name")

            print(f"Procesando archivo desde el bucket: {bucket_name}, clave: {key_name}")

            # Ruta al script externo simulate_glue.py
            script_path = "/var/task/simulate_glue.py"  # Ruta dentro del entorno Lambda

            # Ejecutar el script simulate_glue.py con los argumentos recibidos
            result = subprocess.run(
                ["python3", script_path, bucket_name, key_name],  # Pasar los argumentos
                capture_output=True,  # Capturar la salida para debug
                text=True  # Formatear salida como texto
            )

            # Imprimir la salida del script para fines de debugging
            print(f"Resultado de simulate_glue.py: {result.stdout}")

        except Exception as e:
            print(f"Error al ejecutar simulate_glue.py: {e}")
