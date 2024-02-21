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
    aws_s3 as _s3,
    aws_iam as _iam,
    aws_sqs as _sqs,
    aws_ssm as _ssm
)
from botocore.exceptions import ClientError
from constructs import Construct
from components.fine_tuner import FineTuner
from components.tuning_workflow import Orchestration
from components.fmops_pipeline import Pipeline

class TuningStack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, *, pipeline_name: str, model_parameter: str, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        # Load pipeline variables form toolchain context



        # Define the S3 Bucket for tuning data, and store the name for use outside of the stack



        # Create the Bedrock Service Role to manage the fine-tuning process, and access tuning data



        # Create an SQS queue to integrate the fine-tuning workflow with the FMOps pipeline



        # Add the fine-tuner component



        # Add the Bedrock service role to the fine-tuner handler environment



        # Add the fine-tuning orchestration component



        # Create the FMOps pipeline component



        # Initialize the S3 notification function to start the FMOps pipeline with the context input parameters



        # Initialize the model approval event handler to start the CI/CD process for a tuned model, with permissions
        # to update the model SSM parameter, and start a CodePipeline execution
