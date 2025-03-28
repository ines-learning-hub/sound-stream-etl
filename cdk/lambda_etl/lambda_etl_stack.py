from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    aws_iam as iam,
    Duration,
)
from constructs import Construct

class LambdaETLStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Importar el topic SNS existente
        topic_arn = "arn:aws:sns:us-east-1:000000000000:audio-upload-topic"  # Reemplaza con tu ARN
        topic = sns.Topic.from_topic_arn(self, "ImportedTopic", topic_arn=topic_arn)

        # Crear una cola SQS
        queue = sqs.Queue(
            self, "EtlQueue",
            queue_name="etl-queue",
            visibility_timeout=Duration.seconds(30)  # Tiempo para procesar mensajes
        )

        # Suscribir la cola SQS al topic SNS
        topic.add_subscription(sns_subscriptions.SqsSubscription(queue))

        # Crear la Lambda para procesar los mensajes de SQS
        lambda_fn = _lambda.Function(
            self, "EtlFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            function_name="EtlFunction",
            code=_lambda.Code.from_asset("lambda_etl/lambda_code"),  # Carpeta donde está el código
            handler="handler.main",  # Archivo y función a ejecutar
            timeout=Duration.seconds(30),
            environment={
                "QUEUE_NAME": queue.queue_name,
                "TOPIC_ARN": topic.topic_arn
            }
        )

        # Permitir que la Lambda consuma mensajes de SQS
        queue.grant_consume_messages(lambda_fn)

        # Agregar permisos adicionales si es necesario
        lambda_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "sns:Publish",
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes"
                ],
                resources=[queue.queue_arn, topic.topic_arn]
            )
        )

        # Configurar la Lambda para que escuche la cola SQS automáticamente
        lambda_fn.add_event_source_mapping(
            "SqsEventSource",
            event_source_arn=queue.queue_arn,
            batch_size=1  # Procesar un mensaje a la vez
        )
