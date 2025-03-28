from aws_cdk import (
    Stack,
    Environment,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_notifications as s3_notifications,
    aws_apigateway as apigateway,
    Duration, 
    aws_sns as sns,
    aws_iam as iam,
)
from constructs import Construct
import os
from dotenv import load_dotenv
load_dotenv()

class LambdaS3LocalStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        bucket = s3.Bucket(self, "LocalBucket", bucket_name="my-audio-bucket")
        bucket_out = s3.Bucket(self, "OutputBucket", bucket_name="my-audio-output-bucket")

        topic= sns.Topic(self, "LocalTopic", topic_name="audio-upload-topic")
       
        lambda_fn = _lambda.Function(
            self, "SaveToS3Function",
            runtime=_lambda.Runtime.PYTHON_3_9,
            function_name="SaveToS3Function",
            code=_lambda.Code.from_asset("lambda_s3_local/lambda_code"),
            handler="handler.main",
            timeout=Duration.seconds(10),
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "LOCALSTACK_ENDPOINT": "http://"+os.getenv("IP_ADDRESS")+":4566",
                "TOPIC_ARN":  topic.topic_arn
            }
        )

        bucket.grant_put(lambda_fn)

        # Crear API Gateway y conectar la Lambda
        api = apigateway.RestApi(
            self,"SaveToS3Api",
            rest_api_name="SaveToS3API",
            default_cors_preflight_options={
                "allow_origins": ["*"],  # Permitir solo solicitudes desde localhost:5500
                "allow_methods": ["OPTIONS", "POST"],  # Permitir solo el método POST
                "allow_headers": ["Content-Type"],  # Especificar encabezados permitidos
            },
        )

        # Agregar recurso "items" y habilitar el método POST
        items = api.root.add_resource("items")  # Define /items como recurso
        items.add_method(
            "POST",
            apigateway.LambdaIntegration(lambda_fn),
        )

