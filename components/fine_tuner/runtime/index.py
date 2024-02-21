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
import json
import boto3
import logging

from typing import Dict, Any
from botocore.exceptions import ClientError
from botocore.config import Config

# Global parameters
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)
bedrock_role = os.environ["BEDROCK_ROLE"]
sm_client = boto3.client("sagemaker")
bedrock_client = boto3.client("bedrock")
runtime_client = boto3.client("bedrock-runtime")

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event, indent=2)}")
    if ("status" in event):
        status = event["status"]
    else:
        raise KeyError("'status' parameter not found in event!")
    
    if status == "Start":
        # This is the first time the handler is called, therefore starting the tuning workflow
        job_name, job_arn = start_fine_tuning(event.get("parameters"))
        event["jobName"] = job_name
        event["jobArn"] = job_arn
        event["status"] = "InProgress"
        return event 
    
    elif status == "InProgress":
        # The tuning job is in progress, therefore check, and update the status
        updated_status = check_status(event.get("jobName"))
        event["status"] = updated_status
        return event
    
    elif status == "Completed" or status == "Failed":
        # The tuning job is finished, therefore if successful, return the status
        # (Complete | Failed) to the SageMaker Pipeline
        finalize(event)


def start_fine_tuning(params: Dict) -> Any:
    logger.info(f"Tuning arguments: {params}")
    logger.info("Starting Bedrock Fine Tuning Job ...")
    job_name = f"{params['JOB_PREFIX']}-TuningJob-{params['EXECUTION_ID']}"
        
    try:
        response = bedrock_client.create_model_customization_job(
            jobName=job_name,
            customModelName=f"{params['JOB_PREFIX']}-{params['EXECUTION_ID']}",
            roleArn=bedrock_role,
            baseModelIdentifier=f"arn:aws:bedrock:{os.environ['AWS_DEFAULT_REGION']}::foundation-model/{params['BASE_MODEL']}",
            trainingDataConfig={
                "s3Uri": f"{params['TRAIN_DATA']}/data.jsonl" # NOTE: Hard-coded file `data.jsonl` must correspond to file name in preprocessing script
            },
            validationDataConfig={
                "validators": [
                    {
                        "s3Uri": f"{params['VALIDATION_DATA']}/data.jsonl" # NOTE: Hard-coded file `data.jsonl` must correspond to file name in preprocessing script
                    }
                ]
            },
            outputDataConfig={
                "s3Uri": f"s3://{params['DATA_BUCKET']}/{params['EXECUTION_ID']}"
            },
            hyperParameters=_get_tuning_hyper_parameters(params),
            customModelTags=[
                { 
                    "key": "ExecutionID",
                    "value": params["EXECUTION_ID"]
                }
            ]
        )
        job_arn = response["jobArn"]
        logger.info(f"Tuning Job ARN: {job_arn}")
        return job_name, job_arn
    
    except ClientError as e:
        raise Exception(e.response["Error"]["Message"])
        

def check_status(job_name: str) -> Dict:
    logger.info(f"Checking tuning job status: {job_name}")
    status = bedrock_client.get_model_customization_job(jobIdentifier=job_name)["status"]
    if status in ("Failed", "Stopped", "Stopping"):
        status = "Failed"
    logger.info(f"Tuning status: {status}")
    return status

            
def finalize(event: Dict) -> Dict:
    try:
        # Get tuning job data
        bedrock_response = bedrock_client.get_model_customization_job(jobIdentifier=event.get("jobName"))
        logger.info(f"Tuning job details: {bedrock_response}")
        
        if event["status"] == "Completed":
            # Update callback status to the SageMaker Pipeline
            logger.info("Sending SUCCESSFUL callback to SageMaker Pipeline ...")
            model_name = bedrock_response["outputModelName"]
            sm_client.send_pipeline_execution_step_success(
                CallbackToken=event.get("token"),
                OutputParameters=[
                    {
                        "Name": "OUTPUT_MODEL_NAME",
                        "Value": model_name
                    },
                    {
                        "Name": "OUTPUT_MODEL_ARN",
                        "Value": bedrock_response["outputModelArn"]
                    },
                    {
                        "Name": "JOB_NAME",
                        "Value": bedrock_response["jobName"]
                    },
                    {
                        "Name": "JOB_ARN",
                        "Value": bedrock_response["jobArn"]
                    },
                    {
                        "Name": "BASE_MODEL_ARN",
                        "Value": bedrock_response["baseModelArn"]
                    },
                    {
                        "Name": "OUTPUT_DATA",
                        "Value": bedrock_response["outputDataConfig"]["s3Uri"]
                    }
                ]
            )
        else:
            logger.info("Sending FAILED callback to SageMaker Pipeline ...")
            if bedrock_response["status"] == "Stopped":
                message = "Model customization has been manually stopped"
            else:
                message = bedrock_response["failureMessage"]
            
            sm_client.send_pipeline_execution_step_failure(
                CallbackToken=event.get("token"),
                FailureReason=message
            )

    except ClientError as e:
        message = e.response["Error"]["Message"]
        raise Exception(message)

@staticmethod
def _get_tuning_hyper_parameters(params: Dict) -> Dict:
    model_name = params["BASE_MODEL"]
    hyper_params = {}
    if model_name.startswith("meta.llama2"):
        hyper_params = {
            "epochCount": params["EPOCHS"],
            "batchSize": params["BATCH_SIZE"],
            "learningRate": params["LEARNING_RATE"],
        }
    else:
        hyper_params = {
            "epochCount": params["EPOCHS"],
            "batchSize": params["BATCH_SIZE"],
            "learningRate": params["LEARNING_RATE"],
            "learningRateWarmupSteps": params["WARMUP_STEPS"]
        }
    return hyper_params
