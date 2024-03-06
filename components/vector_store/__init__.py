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

import json
import pathlib
import constants
import aws_cdk as cdk

from aws_cdk import (
    aws_opensearchservice as _opensearch,
    aws_iam as _iam,
    aws_ec2 as _ec2,
    aws_secretsmanager as _secrets,
    aws_s3 as _s3,
    aws_s3_deployment as _deployment,
    aws_lambda as _lambda,
    aws_ecr_assets as _ecr_assets,
    aws_s3_notifications as _notification
)
from constructs import Construct

class VectorStore(Construct):

    def __init__(self, scope: Construct, id: str, data_bucket: _s3.Bucket) -> None:
        super().__init__(scope, id)

        # Load pipeline variables form toolchain context
        context = self.node.try_get_context("toolchain-context")

        # NOTE: The following logic assumes a dedicated OpenSearch environment already exists.
        #       and the necessary configuration has been added to `constants.py`
        if constants.EXISTING_OPENSEARCH_DOMAIN:
            # Create a OpenSearch credentials secret construct from an existing Secrret ARN
            self.opensearch_secret = _secrets.Secret.from_secret_complete_arn(
                self,
                "OpenSearchMasterUserSecret",
                secret_complete_arn=constants.OPENSEARCH_SECRET_ARN
            )

            # Create a domain construct from an existing OpenSearch domain
            self.search_domain = _opensearch.Domain.from_domain_endpoint(
                self,
                "OpenSearchDomain",
                domain_endpoint=constants.OPENSEARCH_ENDPOINT
            )

        else:
            # Create an OpenSearch Master User Secret
            self.opensearch_secret = _secrets.Secret(
                self,
                "OpenSearchMasterUserSecret",
                generate_secret_string=_secrets.SecretStringGenerator(
                    secret_string_template=json.dumps({"USERNAME": "admin"}),
                    generate_string_key="PASSWORD",
                    password_length=8
                )
            )

            # Create the OpenSearch Domain
            self.search_domain = _opensearch.Domain(
                self,
                "OpenSearchDomain",
                version=_opensearch.EngineVersion.OPENSEARCH_2_5,
                ebs=_opensearch.EbsOptions(
                    volume_size=20,
                    volume_type=_ec2.EbsDeviceVolumeType.GP3
                ),
                enforce_https=True,
                node_to_node_encryption=True,
                encryption_at_rest=_opensearch.EncryptionAtRestOptions(
                    enabled=True
                ),
                logging=_opensearch.LoggingOptions(
                    app_log_enabled=True,
                    slow_index_log_enabled=True,
                    slow_search_log_enabled=True
                ),
                fine_grained_access_control=_opensearch.AdvancedSecurityOptions(
                    master_user_name=self.opensearch_secret.secret_value_from_json("USERNAME").unsafe_unwrap(),
                    master_user_password=self.opensearch_secret.secret_value_from_json("PASSWORD")
                ),
                removal_policy=cdk.RemovalPolicy.DESTROY,
                capacity=_opensearch.CapacityConfig(
                    data_node_instance_type="r6g.large.search"
                )
            )
            self.search_domain.add_access_policies(
                _iam.PolicyStatement(
                    principals=[
                        _iam.AnyPrincipal()
                    ],
                    actions=[
                        "es:*"
                    ],
                    effect=_iam.Effect.ALLOW,
                    resources=[
                        self.search_domain.domain_arn,
                        f"{self.search_domain.domain_arn}/*"
                    ]
                )
            )

        # Create the Processing Job image
        processing_image = _ecr_assets.DockerImageAsset(
            self,
            "ProcessingImage",
            directory=str(pathlib.Path(__file__).parent.joinpath("sagemaker_processing_image").resolve()),
            platform=_ecr_assets.Platform.LINUX_AMD64
        )
        
        # Create the SageMaker role for the processing job, with access to the image and S3
        processing_role = _iam.Role(
            self,
            "ProcessingJobRole",
            assumed_by=_iam.CompositePrincipal(
                _iam.ServicePrincipal("sagemaker.amazonaws.com")
            ),
            managed_policies=[
                _iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")
            ],
            inline_policies={
                "BedrockAccess": _iam.PolicyDocument(
                    statements=[
                        _iam.PolicyStatement(
                            actions=[
                                "bedrock:InvokeModel"
                            ],
                            effect=_iam.Effect.ALLOW,
                            resources=[
                                f"arn:aws:bedrock:{cdk.Aws.REGION}::foundation-model/{context.get('bedrock-text-model-id')}",
                                f"arn:aws:bedrock:{cdk.Aws.REGION}::foundation-model/{context.get('bedrock-embedding-model-id')}"
                            ]
                        )
                    ]
                )
            }
        )
        data_bucket.grant_read_write(processing_role)
        processing_image.repository.grant_pull(processing_role)
        self.opensearch_secret.grant_read(processing_role)

        # Create a Lambda function to start the SageMaker Processing Job from S3 notification
        self.notification_function = _lambda.Function(
            self,
            "NotificationFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset(str(pathlib.Path(__file__).parent.joinpath("s3_notification_lambda").resolve())),
            handler="index.lambda_handler",
            timeout=cdk.Duration.seconds(60),
            environment={
                "JOB_NAME": f"{constants.WORKLOAD_NAME}-RAG-Ingest",
                "IMAGE_URI": processing_image.image_uri,
                "ROLE": processing_role.role_arn,
                "SCRIPT_URI": f"s3://{data_bucket.bucket_name}/scripts/data_ingest.py",
                "TEXT_MODEL_ID": context.get("bedrock-text-model-id"),
                "EMBEDDING_MODEL_ID": context.get("bedrock-embedding-model-id"),
                "OPENSEARCH_ENDPOINT": self.search_domain.domain_endpoint,
                "OPENSEARCH_SECRET": self.opensearch_secret.secret_name,
                "OPENSEARCH_INDEX": context.get("embedding-index-name")
            }
        )
        self.notification_function.add_to_role_policy(
            _iam.PolicyStatement(
                sid="StartJobPermission",
                actions=[
                    "sagemaker:CreateProcessingJob",
                    "sagemaker:AddTags",
                    "iam:PassRole"
                ],
                effect=_iam.Effect.ALLOW,
                resources=["*"]
            )
        )

        # Deploy data ingest script to S3
        _deployment.BucketDeployment(
            self,
            "ScriptsDeployment",
            sources=[
                _deployment.Source.asset(
                    path=str(pathlib.Path(__file__).parent.joinpath("scripts").resolve())
                )
            ],
            destination_bucket=data_bucket,
            destination_key_prefix="scripts",
            retain_on_delete=False
        )

        # Add the S3 trigger to start the processing job
        notification = _notification.LambdaDestination(self.notification_function)
        notification.bind(self, bucket=data_bucket)
        data_bucket.add_object_created_notification(
            notification,
            _s3.NotificationKeyFilter(
                suffix=".txt"
            )
        )

    @property
    def endpoint_name(self) -> str:
        return self.search_domain.domain_endpoint
