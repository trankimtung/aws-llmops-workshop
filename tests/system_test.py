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
import requests
import pytest
import constants

def test_text_endpoint():
    # System test for the text api, before deploying into production
    with requests.post(
        os.environ["TEXT_ENDPOINT"],
        json={"question": "What are large language models?"},
        timeout=60
    ) as response:
        assert response.status_code == 200


def test_image_endpoint():
    # System test for the image api, before deploying into production
    with requests.post(
        os.environ["IMAGE_ENDPOINT"],
        json={"prompt": "Dog in a superhero outfit", "style": "digital-art"},
        timeout=180
    ) as response:
        assert response.status_code == 200


def test_web_app():
    # System test for the web application, before deploying into production
    with requests.get(os.environ["APP_ENDPOINT"]) as response:
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/html"


@pytest.mark.skipif(constants.ENABLE_RAG == False, reason="RAG is not enabled")
def test_rag_endpoint():
    # System test for the text api (with RAG), before deploying into production
    # NOTE: This test does NOT test wether the OpenSearch INDEX is hydrated, but simply that the RAG API is functional.
    #       to be initialized, and hydrated
    with requests.post(
        os.environ["RAG_ENDPOINT"],
        json={"question": "what is the address of the fiat customer center"},
        timeout=60
    ) as response:
        assert response.status_code == 200