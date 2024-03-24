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
TEXT_MODEL_ID = os.environ["TEXT_MODEL_ID"]
EMBEDDING_MODEL_ID = os.environ["EMBEDDING_MODEL_ID"]

# Global parameters
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)
bedrock_client = boto3.client("bedrock-runtime")

def lambda_handler(event, context): 
    logger.debug(f"Received event: {json.dumps(event, indent=2)}")
    body = json.loads(event["body"])
    validate_response = validate_inputs(body)
    if validate_response:
        return validate_response
    question = body["question"]
    logger.info(f"Question: {question}")
    response = get_prediction(question=question)
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
    for input_name in ["question"]:
        if input_name not in body:
            return build_response(
                {
                    "status": "error",
                    "message": f"{input_name} missing in payload"
                }
            )


def get_prediction(question: str) -> str:
    logger.info(f"Bedrock model Id: {TEXT_MODEL_ID}")
    logger.info(f"Sending prompt to Bedrock (RAG disabled) ... ")
    if TEXT_MODEL_ID == "anthropic.claude-3-sonnet-20240229-v1:0" or TEXT_MODEL_ID == "anthropic.claude-3-haiku-20240307-v1:0" or TEXT_MODEL_ID == "anthropic.claude-instant-v1":
        response = bedrock_client.invoke_model(
            body=json.dumps(
                {
                    "max_tokens": 4096,
                    "anthropic_version": "bedrock-2023-05-31",
                    "temperature": 0.5,
	                "top_k": 250,
	                "top_p": 1,
                    "system": "You are a helpful assistant answering a human's questions. Provide a concise answer. Use a friendly tone. If the questions cannot be answered, say so. Do not make up answers. Answer the questions immediately without preamble.",
                    "messages": [{"role": "user", "content": question}],
                }
            ),
            modelId=TEXT_MODEL_ID,
            accept="*/*",
            contentType="application/json"
        )
        response_body = json.loads(response.get("body").read())
        answer = response_body.get("content")[0].get("text")
    elif TEXT_MODEL_ID == "meta.llama2-13b-chat-v1" or TEXT_MODEL_ID == "meta.llama2-70b-chat-v1":
        prompt_template = f"""[INST]You are a helpful assistant answering a human's questions. Provide a concise answer. Use a friendly tone. If the questions cannot be answered, say so. Do not make up answers. Answer the questions immediately without preamble.[/INST]\n\n{question}"""
        response = bedrock_client.invoke_model(
            body=json.dumps(
                {
                    "prompt": prompt_template,
                    "max_gen_len": 512,
                    "temperature": 0.5,
                    "top_p": 0.5
                }
            ),
            modelId=TEXT_MODEL_ID,
            accept="*/*",
            contentType="application/json"
        )
        response_body = json.loads(response.get("body").read())
        answer = response_body.get("generation")      
    else:
        # Invoke fine-tuned model
        prompt_template = f"""You are a helpful assistant answering a human's questions. Provide a concise answer. Use a friendly tone. If the questions cannot be answered, say so. Do not make up answers. Answer the questions immediately without preamble.\n\nUser: {question}"""
        response = bedrock_client.invoke_model(
            body=json.dumps(
                {
                    "inputText": prompt_template,
                    "textGenerationConfig": {
                        "maxTokenCount":512,
                        "stopSequences":[],
                        "temperature":0,
                        "topP":0.9
                    }
                }
            ),
            modelId=TEXT_MODEL_ID,
            accept="application/json",
            contentType="application/json"
        )
        response_body = json.loads(response.get("body").read())
        answer = response_body.get("results")[0].get("outputText")
    logger.info(f"Bedrock returned the following answer: {answer}")
    return answer