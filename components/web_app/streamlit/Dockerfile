# Description: Dockerfile for the Streamlit web app

# build stage
FROM public.ecr.aws/docker/library/python:3.10-slim as builder

RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip

WORKDIR /build

RUN python -m venv /opt/python/venv
ENV PATH="/opt/python/venv/bin:$PATH"

COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt


# final stage
FROM public.ecr.aws/docker/library/python:3.10-slim

COPY --from=builder /opt/python/venv /opt/python/venv
ENV PATH="/opt/python/venv/bin:$PATH"

WORKDIR /app
COPY /app .

EXPOSE 8501

ENTRYPOINT [ "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0" ]
