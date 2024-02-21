#!/bin/sh

export WORKLOAD=$(python -c "import constants; print(constants.WORKLOAD_NAME.lower())")
export TUNING_BUCKET=s3://$WORKLOAD-tuning-$AWS_REGION-$AWS_ACCOUNT_ID
aws s3 sync ./tuning-data $TUNING_BUCKET/raw-data/
