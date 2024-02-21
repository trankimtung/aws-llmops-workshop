#!/usr/bin/env python3
import boto3
import constants
import aws_cdk as cdk

from stacks.infrastructure import InfrastructureStack
from stacks.toolchain import ToolChainStack

app = cdk.App()

# Create the TEST infrastructure stack in development environment to verify the generative AI application




# Create the toolchain that defines the CI/CD/CT Pipeline to automate the deployment of QA/PROD envrionment and the TUNING workflow.




app.synth()
