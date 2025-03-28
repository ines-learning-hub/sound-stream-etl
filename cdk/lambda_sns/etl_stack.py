from aws_cdk import (
    aws_lambda as _lambda,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    Duration,
)
from constructs import Construct

class ETLStack(Construct):
    def __init__(self, scope: Construct, id: str, topic_arn: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Crear la Lambda ETL
        lambda_etl = _lambda.Function(
            self, "ETLFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            function_name="ETLFunction",
            code=_lambda.Code.from_asset("path_to_your_etl_code", 
                                         bundling={
                                             "image": _lambda.Runtime.PYTHON_3_9.bundling_docker_image,
                                             "command": ["bash", "-c", "cp -r . /asset-output"]
                                         }),
            handler="handler.main",  
            timeout=Duration.seconds(60),
        )

        # Suscribir la Lambda al SNS Topic
        topic = sns.Topic.from_topic_arn(self, "ExistingTopic", topic_arn)
        topic.add_subscription(
            sns_subscriptions.LambdaSubscription(lambda_etl)
        )
