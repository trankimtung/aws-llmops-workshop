#!/bin/sh
cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess
