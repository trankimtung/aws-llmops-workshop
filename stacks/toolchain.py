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

import constants
import aws_cdk as cdk

from typing import Any
from aws_cdk import (
    pipelines as _pipelines,
    aws_codecommit as _codecommit,
    aws_ssm as _ssm,
    aws_iam as _iam,
    aws_codebuild as _codebuild
)
from stacks.infrastructure import InfrastructureStack
from stacks.tuning import TuningStack
from constructs import Construct

class ToolChainStack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs: Any):
        super().__init__(scope, id, **kwargs)

        # Load pipeline variables form toolchain context



        # Create a CodeCommit repository to be used as the pipeline source code



        # Create a placeholder parameter to store the name of a custom, fine-tuned Titan model



        # Create the CDK Pipeline structure
        


        # Use the `_add_stage()` method to add the QA Stage to the pipeline



        # Use the `_add_stage()` method to add Production Stage to the pipeline



        # Use the `_add_stage()` method to add tuning stack as the Continuous Tuning stage




    @staticmethod
    def _add_stage(pipeline: _pipelines.CodePipeline, stage_name: str, stage_account: str, stage_region: str, model_parameter_name: str=None) -> None:
        stage = cdk.Stage(
            pipeline,
            stage_name,
            env=cdk.Environment(account=stage_account, region=stage_region)
        )
        if stage_name == constants.QA_ENV_NAME:
            infrastructure = InfrastructureStack(
                stage,
                f"{constants.WORKLOAD_NAME}-{stage_name}",
                stack_name=f"{constants.WORKLOAD_NAME}-{stage_name}",
                model_parameter_name=model_parameter_name
            )
            pipeline.add_stage(
                stage,
                post=[
                    _pipelines.ShellStep(
                        "SystemTests",
                        env_from_cfn_outputs={
                            "TEXT_ENDPOINT": infrastructure.text_apigw_output,
                            "RAG_ENDPOINT": infrastructure.rag_apigw_output,
                            "IMAGE_ENDPOINT": infrastructure.image_apigw_output,
                            "APP_ENDPOINT": infrastructure.web_app_url,
                        },
                        install_commands=[
                            "printenv",
                            "python -m pip install -U pip",
                            "pip install -r ./tests/requirements.txt"
                        ],
                        commands=[
                            "pytest ./tests/system_test.py"
                        ]
                    )
                ]
            )
        elif stage_name == constants.PROD_ENV_NAME:
            InfrastructureStack(
                stage,
                f"{constants.WORKLOAD_NAME}-{stage_name}",
                stack_name=f"{constants.WORKLOAD_NAME}-{stage_name}",
                model_parameter_name=model_parameter_name
            )
            pipeline.add_stage(stage)
        else:
            TuningStack(
                stage,
                f"{constants.WORKLOAD_NAME}-{stage_name}",
                stack_name=f"{constants.WORKLOAD_NAME}-{stage_name}",
                pipeline_name=f"{constants.WORKLOAD_NAME}-Pipeline",
                model_parameter=model_parameter_name
            )
            pipeline.add_stage(stage)
