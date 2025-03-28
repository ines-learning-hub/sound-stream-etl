#!/usr/bin/env python3
import aws_cdk as cdk
import ssl
from lambda_s3_local.lambda_s3_local_stack import LambdaS3LocalStack

ssl._create_default_https_context = ssl._create_unverified_context

app = cdk.App()

LambdaS3LocalStack(app, "LambdaS3LocalStack",
    env=cdk.Environment(account="000000000000", region="us-east-1")
)

app.synth()