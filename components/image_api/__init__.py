""" 
MIT No Attribution

Copyright 2023 Amazon.com, Inc. and its affiliates. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import constants
import aws_cdk as cdk

from aws_cdk import (
    aws_iam as _iam,
    aws_lambda as _lambda,
    aws_apigateway as _apigw
)
from constructs import Construct

class ImageApi(Construct):

    def __init__(self, scope: Construct, id: str) -> None:

        super().__init__(scope, id)

        # Load pipeline variables form toolchain context
        context = self.node.try_get_context("toolchain-context")

        # Define the IAM Role for Lambda to invoke the SageMaker Endpoint
        role = _iam.Role(
            self,
            "ImageHandlerRole",
            assumed_by=_iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                _iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                _iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
            ]
        )
        role.attach_inline_policy(
            _iam.Policy(
                self,
                "ImageInvokePolicy",
                statements=[
                    _iam.PolicyStatement(
                        actions=[
                            "bedrock:InvokeModel"
                        ],
                        effect=_iam.Effect.ALLOW,
                        resources=[
                            f"arn:aws:bedrock:{cdk.Aws.REGION}::foundation-model/{context.get('bedrock-image-model-id')}"
                        ]
                    )
                ]
            )
        )

        # Create Lambda Functions for the text2text API
        self.image_handler = _lambda.Function(
            self,
            "ImageHandler",
            code=_lambda.Code.from_asset(
                path="components/image_api/runtime",
                bundling=cdk.BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c", "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            role=role,
            memory_size=512,
            timeout=cdk.Duration.seconds(300)
        )

        # Create the API Gateway 
        self.image_apigw = _apigw.LambdaRestApi(
            self,
            "ImageApiGateway",
            handler=self.image_handler
        )
