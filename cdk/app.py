#!/usr/bin/env python3
import aws_cdk as cdk
from lambda_s3_local.lambda_s3_local_stack import LambdaS3LocalStack

app = cdk.App()

LambdaS3LocalStack(app, "LambdaS3LocalStack",
    env=cdk.Environment(account="000000000000", region="us-east-1")
)

app.synth()