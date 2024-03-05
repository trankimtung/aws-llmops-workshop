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
import io
import base64
import requests
import streamlit as st

from PIL import Image

# Initialization
HTTP_OK = 200
text_api = os.getenv("TEXT_API", "") # Enter api url for integration testing
rag_api = os.getenv("RAG_API", "") # Enter api url for integration testing
image_api = os.getenv("IMAGE_API", "") # Enter api url for integration testing
headers = {"accept": "application/json", "Content-Type": "application/json"}
style_presets = [
    "pixel-art",
    "photographic",
    "fantasy-art",
    "digital-art",
    "anime",
    "3d-model",
    "analog-film", 
    "cinematic", 
    "comic-book",
    "enhance",
    "isometric",
    "line-art",
    "low-poly",
    "modeling-compound",
    "neon-punk",
    "origami",
    "tile-texture"
]
if "zero" not in st.session_state:
    st.session_state["zero"] = ""
if "db" not in st.session_state:
    st.session_state["db"] = ""

# Bedrock standard request
def zero_shot(query: str) -> str:
    with st.spinner("Thinking ..."):
        data = {"question": query}
        response = requests.post(text_api, headers=headers, json=data, timeout=120)
        if response.status_code != HTTP_OK:
            st.session_state["zero"] = response.text

        else:
            st.session_state["zero"] = response.json()["response"]

# RAG request
def use_db(query: str) -> str:
    with st.spinner("Thinking ..."):
        data = {"question": query}
        if not rag_api:
            st.session_state["db"] = ":red[Retrieval Augmented Generation (RAG) has not been enabled!]"
            return
        
        response = requests.post(rag_api, headers=headers, json=data, timeout=120)
        if response.status_code != HTTP_OK:
            st.session_state["db"] = response.text
        
        else:
            st.session_state["db"] = response.json()["response"]

st.set_page_config(layout="wide", page_icon=":robot:", page_title="Generative AI Demo")
st.header("Generative AI Demo Application - Image and Text Generation")
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden; }
    footer {visibility: hidden;}
        [data-testid=stSidebar] [data-testid=stImage] {
            text-align: center;
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 80%;
        }
    </style>
    """, unsafe_allow_html=True)
st.sidebar.image("./img/logo.png", width=100)
st.sidebar.divider()

with st.sidebar:
    st.markdown('''
        This demo web application is designed to showcase two possible use cases for Generative AI: __Image Generation__ and __Questions & Answers__.  
        
        To generate images, go to the __Image Generation__ tab. Enter a description of the image you want to generate in the text area. 
        Then, select the style preset for the generated image from the drop-down menu.
        Click the `Generate image` button to create the image.  
        
        To ask questions, go to the __Questions & Answers__ tab. Enter your question in the text area.
        Check the box to enable Retrieval Augmented Generation, and click the `Submit` button. 
    ''')

tab1, tab2 = st.tabs(["Image Generation", "Questions & Answers"])
with tab1:
    st.subheader("Generate Image")
    prompt = st.text_area("Input Image description:")
    style = st.selectbox(label="Select the image style preset:", options=style_presets)

    if st.button("Generate image"):
        if prompt == "":
            st.error("Please enter a valid prompt!")

        else:
            with st.spinner("Generating something nice ..."):
                try:
                    response = requests.post(image_api, json={"prompt": prompt, "style": style}, timeout=180)
                    response_body = response.json()["response"]
                    image = Image.open(io.BytesIO(base64.decodebytes(bytes(response_body, "utf-8"))))
                    st.image(image)

                except requests.exceptions.ConnectionError as errc:
                    st.error("Error Connecting:",errc)
                    
                except requests.exceptions.HTTPError as errh:
                    st.error("Http Error:",errh)
                    
                except requests.exceptions.Timeout as errt:
                    st.error("Timeout Error:",errt)    
                    
                except requests.exceptions.RequestException as err:
                    st.error("OOps: Something Else",err)

with tab2:
    st.subheader("Question & Answer Text Generation")
    form = st.form(key="Form", clear_on_submit=False)
    with form:
        prompt= st.text_area("Enter your question here:", height=100)
        left, right = st.columns(2)
        db = st.checkbox("Use database for additional context (RAG)")
        submit_button = form.form_submit_button("Submit")
        if submit_button:
            if prompt != "" and not db:
                zero_shot(query=prompt)
                st.write(st.session_state.zero)

            elif prompt != "" and db:
                use_db(query=prompt)
                st.write(st.session_state.db)

            else:
                st.error("Question field cannot be empty!")
