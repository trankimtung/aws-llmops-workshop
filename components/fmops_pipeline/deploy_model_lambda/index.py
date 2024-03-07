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

import os
import boto3
import json
import logging

from typing import Any
from botocore.exceptions import ClientError

# Global parameters
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event, indent=2)}")
    """
    NOTE: The following code is specific to the workshop where there is no enforcing 
    the workshop attendee to puschase, and configure provisioned throughput.
    """
    pipeline_name = os.environ["PIPELINE_NAME"]
    model_name = event["detail"]["CustomerMetadataProperties"]["ModelName"]
    model_parameter_name = os.environ["MODEL_PARAMETER"]
    update_parameter(
        parameter_name=model_parameter_name,
        model_name=model_name
    )
    pipeline_execution_id = start_pipeline(name=pipeline_name)
    
    """
    NOTE: The following code mirrors a real-world scenario where the ML practitioner
    purchases, and configures provisioned throughput for the custom model.
    """
    # logger.info("Getting Provisioned Throughput model ARN ...")
    # model_id = get_model_arn(
    #     model_name=event["detail"]["CustomerMetadataProperties"]["ModelName"]
    # )
    # logger.info(f"Provisioned Throughput model: {model_id}")
    # update_parameter(
    #     parameter_name=os.environ["MODEL_PARAMETER"],
    #     model_name=model_id
    # )
    # logger.info("Executing release change of CI/CD Pipeline ...")
    # pipeline_execution_id = start_pipeline(
    #     name=os.environ["PIPELINE_NAME"]
    # )
    return {
        "statusCode": 200,
        "body": pipeline_execution_id
    }


def get_model_arn(model_name: str) -> str:
    bedrock_client = boto3.client("bedrock")
    try:
        # Get the custom model details for the approved custom model
        custom_model = bedrock_client.list_custom_models(
            nameContains=model_name
        )
        # Get the provisioned throughput resource for the `custom_model`
        provisioned_models = bedrock_client.list_provisioned_model_throughputs(
            statusEquals="InService",
            sortBy="CreationTime",
            sortOrder="Descending"
        )
        # Return the ARN for the provisioned model as the new model ID for inference
        for model in provisioned_models["provisionedModelSummaries"]:
            if model["modelArn"] == custom_model["modelSummaries"][0]["modelArn"]:
                return model["provisionedModelArn"]

    except ClientError as e:
        raise Exception(e.response["Error"]["Message"])


def update_parameter(parameter_name: str, model_name: str) -> Any:
    logger.info("Updating SSM Parameter with new model custom model name ...")
    ssm_client = boto3.client("ssm")
    try:
        ssm_client.put_parameter(
            Name=parameter_name,
            Value=model_name,
            Overwrite=True
        )
    
    except ClientError as e:
        raise Exception(e.response["Error"]["Message"])


def start_pipeline(name: str) -> str:
    logger.info("Executing CI/CD pipeline with new model ...")
    cp_client = boto3.client("codepipeline")
    try:
        response = cp_client.start_pipeline_execution(
            name=name
        )
        execution_id = response["pipelineExecutionId"]
        logger.info(f"Pipeline Execution ID: {execution_id}")
        return execution_id
    
    except ClientError as e:
        raise Exception(e.response["Error"]["Message"])
