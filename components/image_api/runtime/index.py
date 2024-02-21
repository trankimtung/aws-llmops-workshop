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

from typing import Dict
from botocore.config import Config

# Environmental parameters
IMAGE_MODEL_ID = os.environ["IMAGE_MODEL_ID"]

# Global parameters
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)
cfg_scale = 5 # How strictly the diffusion process adheres to the prompt text
seed = 0 # Random seed omitted
steps = 70 # No. of diffusion steps
negative_prompts = [
    "poorly rendered",
    "poor background details",
    "poorly drawn images",
    "disfigured features"
]
bedrock_client = boto3.client("bedrock-runtime")

def lambda_handler(event, context): 
    logger.debug(f"Received event: {json.dumps(event, indent=2)}")
    body = json.loads(event["body"])
    validate_response = validate_inputs(body)
    if validate_response:
        return validate_response
    prompt = body["prompt"]
    style = body["style"]
    logger.info(f"Prompt: {prompt}")
    response = get_prediction(prompt, style)
    return build_response(
        {
            "response": response
        }
    )


def build_response(body: Dict) -> Dict:
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }


def validate_inputs(body: Dict):
    for input_name in ["prompt", "style"]:
        if input_name not in body:
            return build_response(
                {
                    "status": "error",
                    "message": f"{input_name} missing in payload"
                }
            )


def get_prediction(prompt: str, style: str) -> str:
    logger.info(f"Sending prompt to Bedrock ... ")
    response = bedrock_client.invoke_model(
        body=json.dumps(
            {
                "text_prompts": (
                    [
                        {
                            "text": prompt,
                            "weight": 1.0
                        }
                    ]
                    + [
                        {
                            "text": negative_prompt,
                            "weight": -1.0
                        } for negative_prompt in negative_prompts
                    ]
                ),
                "cfg_scale": cfg_scale,
                "seed": seed,
                "steps": steps,
                "style_preset": style
            }
        ),
        modelId=IMAGE_MODEL_ID,
        contentType="application/json",
        accept="application/json"
    )
    response_body = json.loads(response.get("body").read())
    logger.info(response_body)
    image = response_body["artifacts"][0].get("base64")
    logger.info(f"Bedrock returned the following base64 image array: {image}")
    return image
