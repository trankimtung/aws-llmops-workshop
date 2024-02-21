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

from botocore.exceptions import ClientError

# Global parameters
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)
sm_client = boto3.client("sagemaker")
sfn_client = boto3.client("stepfunctions")


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event, indent=2)}")
    for record in event["Records"]:
        payload = json.loads(record["body"])
        if payload.get("status") != "Stopping":
            logger.info("Starting State Machine Execution ...")
            try:
                response = sfn_client.start_execution(
                    stateMachineArn=os.environ["STATE_MACHINE_ARN"],
                    input=json.dumps(
                        {
                            "status": "Start",
                            "parameters": payload.get("arguments"),
                            "token": payload.get("token")
                        }
                    )
                )
                execution_arn = response["executionArn"]
                logger.info(f"Execution ARN: {execution_arn}")
                return {
                    "statusCode": 200,
                    "body": execution_arn
                }
            
            except ClientError as e:
                message = e.response["Error"]["Message"]
                raise Exception(message)
        else:
            try:
                sm_client.send_pipeline_execution_step_failure(
                    CallbackToken=payload.get("token"),
                    FailureReason="Manual Stopping Behavior"
                )
            
            except ClientError as e:
                message = e.response["Error"]["Message"]
                raise Exception(message)
