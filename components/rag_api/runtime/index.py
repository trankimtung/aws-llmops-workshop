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
import requests

from typing import Optional, Dict, List, Tuple, Any
from botocore.config import Config
from botocore.exceptions import ClientError
from requests.auth import HTTPBasicAuth

# Environmental parameters
TEXT_MODEL_ID = os.environ["TEXT_MODEL_ID"]
EMBEDDING_MODEL_ID = os.environ["EMBEDDING_MODEL_ID"]
OPENSEARCH_ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT", None)
OPENSEARCH_SECRET = os.getenv("OPENSEARCH_SECRET", None)
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", None)

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
    response = get_prediction(
        question=question
    )
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
                    "message": f"{input_name} missing in request payload"
                }
            )


def verify_index(endpoint: str, index: str, username: str, password: str) -> Any:
    url = f"{endpoint}/{index}"
    response = requests.head(url, auth=HTTPBasicAuth(username, password))
    if response.status_code != 200:
        logger.info("Embedding index unavailable. RAG data ingest required.")
        return build_response(
            {
                "status": "error",
                "message": "The vector store is not hydrated. Please contact your System Administrator to ingest RAG data."
            }
        )


def get_credentials(secret_id: str, region: str) -> str:
    client = boto3.client("secretsmanager", region_name=region)
    try:
        response = client.get_secret_value(SecretId=secret_id)
        json_body = json.loads(response["SecretString"])
        return json_body["USERNAME"], json_body["PASSWORD"]
    except ClientError as e:
        message = e.response["Error"]["Message"]
        logger.error(message)
        return build_response(
            {
                "status": "error",
                "message": message
            }
        )


def get_embedding(passage: str) -> List[float]:
    body = json.dumps(
        {
            "inputText": f"{passage}"
        }
    )
    try:
        request = bedrock_client.invoke_model(
            body=body,
            modelId=EMBEDDING_MODEL_ID,
            accept="application/json",
            contentType="application/json"
        )
        response = json.loads(request.get("body").read())
        embedding = response.get("embedding")
        return embedding
    except ClientError as e:
        message = e.response["Error"]["Message"]
        logger.error(message)
        return build_response(
            {
                "status": "error",
                "message": message
            }
        )


def get_hits(query: str, url: str, username: str, password: str) -> List[dict]:
    k = 5  # Retrieve top 5 matching context from search
    search_query = {
        "size": k,
        "query": {
            "knn": {
                "vector_field": { # k-NN vector field
                    "vector": get_embedding(query),
                    "k": k
                }
            }
        }
    }
    response = requests.post(
        url=url,
        auth=HTTPBasicAuth(username, password),
        json=search_query
    ).json()
    hits = response["hits"]["hits"]
    return hits


def get_prediction(question: str) -> str:
    region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION"))
    domain_endpoint = f"https://{OPENSEARCH_ENDPOINT}" if not OPENSEARCH_ENDPOINT.startswith("https://") else OPENSEARCH_ENDPOINT
    logger.info(f"Retrieving OpenSearch credentials ...")
    username, password = get_credentials(OPENSEARCH_SECRET, region)
    logger.info("Verifying embedding index exists ...")
    verify_response = verify_index(endpoint=domain_endpoint, index=OPENSEARCH_INDEX, username=username, password=password)
    if verify_response:
        return verify_response
    search_url = f"{domain_endpoint}/{OPENSEARCH_INDEX}/_search"
    
    logger.info(f"Embedding index exists, retrieving query hits from OpenSearch endpoint: {search_url}")
    hits = get_hits(query=question, url=search_url, username=username, password=password)
    
    logger.info("The following documents were returned from OpenSearch:")
    for hit in hits:
        logging.info(f"Score: {hit['_score']} | Document: {hit['_source']['file_name']} | Passage: {hit['_source']['passage']}\n")
    
    logger.info(f"Sending prompt to Bedrock (Using OpenSearch context) ...")
    context = "\n".join([hit["_source"]["passage"] for hit in hits])

    logger.info(f"Bedrock model Id: {TEXT_MODEL_ID}")

    if TEXT_MODEL_ID == "anthropic.claude-3-sonnet-20240229-v1:0" or TEXT_MODEL_ID == "anthropic.claude-instant-v1":
        answer = invoke_anthropic_model(question=question, context=context)
    else:
        logger.info(f"Model is not supported: {TEXT_MODEL_ID}")
        answer = build_response(
            {
                "status": "error",
                "message": f"Model is not supported: {TEXT_MODEL_ID}"
            }
        )

    logger.info(f"Bedrock returned the following answer: {answer}")
    return answer

def invoke_anthropic_model(question: str, context: str) -> Any:
    prompt = f"""I'm going to give you a document. Then I'm going to ask you a question about it. I'd like you to first write down exact quotes of parts of the document that would help answer the question, and then I'd like you to answer the question using facts from the quoted content. Here is the document:

    <document>
    {context}
    </document>

    First, find the quotes from the document that are most relevant to answering the question, and then print them in numbered order. Quotes should be relatively short.

    If there are no relevant quotes, write "No relevant quotes" instead.

    Then, answer the question, starting with "Answer:". Unless you are aksed to quote the document, do not include or reference quoted content verbatim in the answer. Don't say "According to Quote [1]" when answering. Instead make references to quotes relevant to each section of the answer solely by adding their bracketed numbers at the end of relevant sentences.

    Thus, the format of your overall response should look like what's shown between the <example></example> tags. Make sure to follow the formatting, spacing and line breaking exactly.

    <example>
    Relevant quotes:\n
    [1] "Company X reported revenue of $12 million in 2021."\n
    [2] "Almost 90% of revene came from widget sales, with gadget sales making up the remaining 10%."\n

    Answer:\n
    Company X earned $12 million. [1]  Almost 90% of it was from widget sales. [2]
    </example>

    Here is the question: {question}

    If the question cannot be answered by the document, say so.
    
    Answer the question immediately without preamble.
    """

    response = bedrock_client.invoke_model(
        body=json.dumps(
            {
                "max_tokens": 8192,
                "anthropic_version": "bedrock-2023-05-31",
                "temperature": 0.5,
                "top_k": 250,
                "top_p": 1,
                "messages": [{"role": "user", "content": prompt}],
            }
        ),
        modelId=TEXT_MODEL_ID,
        accept="*/*",
        contentType="application/json"
    )
    response_body = json.loads(response.get("body").read())
    return response_body.get("content")[0].get("text")

