#!/bin/sh
export WORKLOAD=$(python -c "import constants; print(constants.WORKLOAD_NAME.lower())")
export RAG_BUCKET=s3://$WORKLOAD-prod-rag-$AWS_REGION-$AWS_ACCOUNT_ID
aws s3 cp ./rag-data/additional-context.txt $RAG_BUCKET/