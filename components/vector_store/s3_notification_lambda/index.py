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
import time

from botocore.exceptions import ClientError

# Global parameters
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)
sm_client = boto3.client("sagemaker")

# Environmental parameters
job_name = os.environ["JOB_NAME"]
region = os.environ["AWS_DEFAULT_REGION"]
image_uri = os.environ["IMAGE_URI"]
job_role_arn = os.environ["ROLE"]
script_path = os.environ["SCRIPT_URI"]
text_model = os.environ["TEXT_MODEL_ID"]
embedding_model = os.environ["EMBEDDING_MODEL_ID"]
opensearch_endpoint = os.environ["OPENSEARCH_ENDPOINT"]
opensearch_secret = os.environ["OPENSEARCH_SECRET"]
opensearch_index = os.environ["OPENSEARCH_INDEX"]

def lambda_handler(event, context):
    logger.debug(f"Received event: {json.dumps(event, indent=2)}")
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    version_id = event["Records"][0]["s3"]["object"]["versionId"]
    current_time = time.strftime("%m-%d-%H-%M-%S", time.localtime())
    try:
        print("Starting SageMaker processing job ...")
        response = sm_client.create_processing_job(
            ProcessingInputs=[
                {
                    'InputName': 'code',
                    'S3Input': {
                        'S3Uri': script_path,
                        'LocalPath': '/opt/ml/processing/input/code',
                        'S3DataType': 'S3Prefix',
                        'S3InputMode': 'File',
                        'S3DataDistributionType': 'FullyReplicated',
                        'S3CompressionType': 'None'
                    }
                },
                {
                    'InputName': 'data',
                    'S3Input': {
                        'S3Uri': f"s3://{bucket}/{key}",
                        'LocalPath': '/opt/ml/processing/input/data',
                        'S3DataType': 'S3Prefix',
                        'S3InputMode': 'File',
                        'S3DataDistributionType': 'FullyReplicated',
                        'S3CompressionType': 'None'
                    }
                }
            ],
            ProcessingOutputConfig={
                'Outputs': [
                    {
                        'OutputName': 'logs',
                        'S3Output': {
                            'S3Uri': f"s3://{bucket}/processing-logs/{job_name}-{current_time}",
                            'LocalPath': '/opt/ml/processing/output',
                            'S3UploadMode': 'EndOfJob'
                        }
                    }
                ]
            },
            ProcessingJobName=f"{job_name}-{current_time}",
            ProcessingResources={
                'ClusterConfig': {
                    'InstanceCount': 1,
                    'InstanceType': 'ml.m5.xlarge',
                    'VolumeSizeInGB': 20,
                }
            },
            StoppingCondition={
                'MaxRuntimeInSeconds': 1800
            },
            AppSpecification={
                'ImageUri': image_uri,
                'ContainerEntrypoint': [
                    'python',
                    '/opt/ml/processing/input/code/data_ingest.py'
                ],
                'ContainerArguments': [
                    '--text-model', text_model,
                    '--embedding-model', embedding_model,
                    '--opensearch-domain', opensearch_endpoint,
                    '--opensearch-secret', opensearch_secret,
                    '--opensearch-index', opensearch_index,
                    '--region', region
                ]
            },
            RoleArn=job_role_arn,
            Tags=[
                {
                    'Key': 'DataVersionId',
                    'Value': version_id
                }
            ]
        )

        return {
            "statusCode": 200,
            "body": response["ProcessingJobArn"]
        }

    except ClientError as e:
        message = e.response["Error"]["Message"]
        raise Exception(message)
