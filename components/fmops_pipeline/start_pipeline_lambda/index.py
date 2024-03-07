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
import time
import logging

from botocore.exceptions import ClientError

# Global parameters
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)
sm_client = boto3.client("sagemaker")

def lambda_handler(event, context):
    logger.debug(f"Received event: {json.dumps(event, indent=2)}")
    logger.info("Starting SageMaker Pipeline Execution ...")
    try:
        response = sm_client.start_pipeline_execution(
            PipelineName=os.environ["PIPELINE_NAME"],
            PipelineParameters=[
                {"Name": "BaseModel", "Value": os.environ["BASE_MODEL"]},
                {"Name": "DataBucket", "Value": event["Records"][0]["s3"]["bucket"]["name"]},
                {"Name": "DataPrefix", "Value": event["Records"][0]["s3"]["object"]["key"]},
                {"Name": "Epochs", "Value": str(os.environ["EPOCHS"])},
                {"Name": "BatchSize", "Value": str(os.environ["BATCHES"])},
                {"Name": "LearningRate", "Value": str(os.environ["LEARNING_RATE"])},
                {"Name": "WarmupSteps", "Value": str(os.environ["WARMUP_STEPS"])}
            ]
        )
        execution_arn = response["PipelineExecutionArn"]
        logger.info(f"SageMaker Pipeline Execution ARN: {execution_arn}")
        return {
            "statusCode": 200,
            "body": execution_arn
        }
    
    except ClientError as e:
        message = e.response["Error"]["Message"]
        raise Exception(message)
