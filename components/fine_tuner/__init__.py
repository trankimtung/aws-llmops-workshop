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
import aws_cdk as cdk

from aws_cdk import (
    aws_iam as _iam,
    aws_lambda as _lambda
)
from constructs import Construct

class FineTuner(Construct):

    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)

        # Create the Fine Tuning handler role
        tuning_handler_role = _iam.Role(
            self,
            "TuningHandlerRole",
            assumed_by=_iam.CompositePrincipal(
                _iam.ServicePrincipal("lambda.amazonaws.com"),
                _iam.ServicePrincipal("bedrock.amazonaws.com"),
                _iam.ServicePrincipal("sagemaker.amazonaws.com")
            ),
            managed_policies=[
                _iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                _iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
            ],
            inline_policies={
                "BedrockAccess": _iam.PolicyDocument(
                    statements=[
                        _iam.PolicyStatement(
                            actions=[
                                "bedrock:DeleteCustomModel",
                                "bedrock:CreateModelCustomizationJob",
                                "bedrock:StopModelCustomizationJob",
                                "bedrock:GetCustomModel",
                                "bedrock:GetModelCustomizationJob",
                                "bedrock:ListModelCustomizationJobs",
                                "bedrock:ListCustomModels",
                                "bedrock:InvokeModel",
                                "bedrock:TagResource"
                            ],
                            effect=_iam.Effect.ALLOW,
                            resources=["*"]
                        )
                    ]
                ),
                "SageMakerPipelineAccess": _iam.PolicyDocument(
                    statements=[
                        _iam.PolicyStatement(
                            actions=[
                                "sagemaker:SendPipelineExecutionStepSuccess",
                                "sagemaker:SendPipelineExecutionStepFailure"
                            ],
                            effect=_iam.Effect.ALLOW,
                            resources=[
                                f"arn:{cdk.Aws.PARTITION}:sagemaker:*:{cdk.Aws.ACCOUNT_ID}:pipeline/*/execution/*"
                            ]
                        )
                    ]
                ),
                "PassRole": _iam.PolicyDocument(
                    statements=[
                        _iam.PolicyStatement(
                            actions=["iam:PassRole"],
                            effect=_iam.Effect.ALLOW,
                            resources=["*"]
                        )
                    ]
                )
            }
        )

        # Create the Fine tuning handler
        self.fine_tuner_handler = _lambda.Function(
            self,
            "TuningHandler",
            code=_lambda.Code.from_asset(
                path="components/fine_tuner/runtime",
                bundling=cdk.BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c", "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            role=tuning_handler_role,
            memory_size=512,
            timeout=cdk.Duration.seconds(60)
        )
