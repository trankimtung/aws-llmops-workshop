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

import boto3
import constants
import aws_cdk as cdk

from aws_cdk import (
    aws_ec2 as _ec2,
    aws_s3 as _s3,
    aws_ssm as _ssm
)
from typing import Dict
from constructs import Construct
from components.text_api import TextApi
from components.rag_api import RagApi
from components.image_api import ImageApi
from components.web_app import WebApp
from components.vector_store import VectorStore

class InfrastructureStack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, *, model_parameter_name: str=None, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        # Load pipeline variables for the toolchain context from `cdk.json`



        # Create VPC across 2 AZ's, to host the ECS cluster for the Web Application.



        # Define the Bedrock Text API using the pre-built `TextAPI` component



        # Expose the Text API Endpoint as a CloudFormation output, for use during system testing



        # Define the Bedrock Image API using the pre-built `ImageApi` component



        # Expose the Image API Endpoint as a CloudFormation output, for use during system testing



        # Create RAG tuning resources, IF the solution constant `ENABLE_RAG` is set to `True`



        # Create the streamlit application. This is the application where users will prompt the LLM



        # Expose the DNS URL for the streamlit web application



    @staticmethod
    def _get_model(parameter_name: str, region: str, context: Dict) -> str:
        # Return the model context if deploying the infrastructure in DEV/TEST
        if parameter_name == None:
            return context.get("bedrock-text-model-id")

        # Return the model context within the CI/CD/CT toolchain
        try:
            ssm_client = boto3.client("ssm", region_name=region)
            response = ssm_client.get_parameter(
                Name=parameter_name
            )
            model = response["Parameter"]["Value"]
            if model == "PLACEHOLDER":
                # There is no custom model, therefore return context default
                return context.get("bedrock-text-model-id")
            else:
                # Custom tuned model exists from continuous tuning stack
                return model
        except ssm_client.exceptions.ParameterNotFound:
            # The model parameter doesn't exist, meaning the Infrastructure stack has not been
            # deployed within the context of the CI/CD/CT toolchain
            return context.get("bedrock-text-model-id")