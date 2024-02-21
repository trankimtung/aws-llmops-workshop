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

import pathlib
import constants
import aws_cdk as cdk

from aws_cdk import(
    aws_ec2 as _ec2,
    aws_ecs as _ecs,
    aws_iam as _iam,
    aws_ecs_patterns as _patterns
)
from constructs import Construct
from typing import Dict


class WebApp(Construct):

    def __init__(self, scope: Construct, id: str, vpc: _ec2.Vpc, text_endpoint: str, image_endpoint: str, rag_endpoint: str) -> None:
        super().__init__(scope, id)

        # Create an ECS Cluster
        cluster = _ecs.Cluster(self, "EcsCluster", vpc=vpc)

        # Create a Fargate Task definition to host the web application
        definition = _ecs.FargateTaskDefinition(
            self,
            "TaskDefinition",
            task_role=_iam.Role(
                self,
                "TaskRole",
                assumed_by=_iam.CompositePrincipal(
                    _iam.ServicePrincipal("ecs-tasks.amazonaws.com")
                )
            ),
            memory_limit_mib=2048,
            cpu=512,
            runtime_platform=_ecs.RuntimePlatform(
                operating_system_family=_ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=_ecs.CpuArchitecture.X86_64
            )
        )
        definition.add_to_execution_role_policy(
            statement=_iam.PolicyStatement(
                actions=[
                    "ecr:getauthorizationtoken",
                    "ecr:batchchecklayeravailability",
                    "ecr:getdownloadurlforlayer",
                    "ecr:batchgetimage",
                    "logs:createlogstream",
                    "logs:putlogevents"
                ],
                effect=_iam.Effect.ALLOW,
                resources=["*"]
            )
        )
        definition.add_container(
            "WebAppImage",
            image=_ecs.ContainerImage.from_asset(
                directory=str(pathlib.Path(__file__).parent.joinpath("streamlit").resolve())
            ),
            logging=_ecs.AwsLogDriver(
                stream_prefix="ecs-logs"
            ),
            port_mappings=[
                _ecs.PortMapping(
                    container_port=8501
                )
            ],
            environment={
                "TEXT_API": text_endpoint,
                "IMAGE_API": image_endpoint,
                "RAG_API": rag_endpoint
            }
        )

        # Create the Fargate service
        self.service = _patterns.ApplicationLoadBalancedFargateService(
            self,
            "FargateService",
            cluster=cluster,
            task_definition=definition,
            desired_count=1,
            public_load_balancer=True
        )
        
        # Enable Autoscaling for the Fargate service
        query_scaling = self.service.service.auto_scale_task_count(
            max_capacity=10
        )
        query_scaling.scale_on_cpu_utilization(
            "CpuAutoScaling",
            target_utilization_percent=50,
            scale_in_cooldown=cdk.Duration.seconds(60),
            scale_out_cooldown=cdk.Duration.seconds(60),
        )
