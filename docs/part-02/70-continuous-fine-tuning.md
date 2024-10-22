# Continuous Fine-tuning

In this chapter of the workshop you will learn how to add a continuous fine-tuning stage to the CI/CD pipeline, and how to automate the LLM fine-tuning process using Amazon SageMaker Pipelines and Amazon Bedrock.

# Introduction to Continuous Fine-tuning

__Continuous Fine-tuning__ is a process in machine learning where a pre-trained model is continually updated or refined using new data over time, without retraining the entire model from scratch. This approach allows the model to adapt to changing circumstances, preferences, or requirements without the need for resource-intensive retraining.

__Continuous Fine-tuning__ deviates from __Continuous Training__, where continuous training involves retraining the entire model periodically, while continuous fine-tuning involves making incremental updates to the existing model using small batches of new data.

On AWS, __Continuous Training__ process can be automated using Amazon SageMaker Pipelines, as illustrated in the image below. When a new training dataset is provided, either in Amazon S3 or another designated location, a SageMaker pipeline is executed to automate the steps of pre-processing the data, starting a SageMaker training job, evaluating the model, and if the evaluation metric shows improvement, register the model version in the model registry. The model can then be used within the application.

![](../img/continuous-training.png)

- __Continuous Training__:
    - Involves retraining the entire model periodically or in response to significant changes in the data or business requirements.
    - It typically entails collecting new data, retraining the model from scratch using the combined old and new data, and deploying the updated model to production.
    - More resource-intensive and time-consuming compared to fine-tuning, as it involves training the entire model with a large dataset.

- __Continuous Fine-tuning__:
    - Focuses on making incremental updates to the existing model by adjusting its parameters using small batches of new data.
    - Instead of retraining the entire model from scratch, fine-tuning involves leveraging techniques like transfer learning or online learning to update the model's weights or parameters based on new information.
    - Is less resource-intensive and faster than continuous training, making it suitable for scenarios where frequent updates are needed without significant changes to the model architecture.

The choice between the two depends on factors such as the frequency of data updates, computational resources, and the need for model stability versus adaptability. In this workshop, we will focus on Continuous Fine-tuning.

# Continuous Fine-tuning with Amazon SageMaker Pipelines and Amazon Bedrock

In this workshop you will use the foundation models provided by Amazon Bedrock. Bedrock supports fine-tuning various foundation models using your fine-tuning dataset to enhance model performance on domain-specific tasks. You will automate the fine-tuning process using Amazon SageMaker Pipelines, the process is mostly similar to the continuous training process illustrated above, the different is that the training step now becomes a fine-tuning step.

The following diagram illustrates the automated fine-tuning process and the architecture you will create in this chapter:

![](../img/architecture-with-continuos-tuning.png)

You will notice that the fine-tuning step of the SageMaker Pipeline is backed by an Amazon SQS Queue and an AWS Step Functions State Machine. This is because Amazon SageMaker Pipelines does not offer direct integration with Amazon Bedrock for fine-tuning yet. The SQS queue acts as the bridge between the SageMaker Pipeline and the Bedrock fine-tuning jobs. The Step Functions State Machine coordinates the fine-tuning jobs, and reports the status back to the SageMaker Pipeline.

When a fine-tuning dataset is uploaded to the tuning S3 bucket, the SageMaker Pipeline is triggered. The pipeline then runs a SageMaker Processing job to read the fine-tuning data and split it into separate training and validation datasets. Once these datasets are created and stored in the tuning S3 bucket, these data dependencies are passed onto the `Fine-Tuning` step. The `Fine-Tuning` step is a SageMaker Callback Step, which uses SQS to send a message to the Step Functions State Machine which orchestrates the Bedrock model fine-tuning job, using the train and validation datasets from the `Pre-processing` step. The execution of the Step Function State Machine can be viewed by searching for and clicking on the Step Functions service console. Once the Bedrock fine-tuning job has completed, the SageMaker Pipeline evaluates the performance metrics associated with the fine-tuned model and stores the fine-tuned model metadata in the SageMaker Model Registry. At this step, Data Scientists, or ML practitioners can evaluate the new model version to determine whether it is a viable candidate for production release. Upon approving the fine-tuned model version, the CI/CD pipeline automates the re-deployment of the demo Generative AI application to leverage the fine-tuned model.

> Once a fine-tuned is approved for production and the CI/CD pipeline is triggered, the value of the Amazon Systems Manager Parameter Store parameter `CustomModelName` is updated from `PLACEHOLDER` to the name of the fine-tuned model. After being redeployed, the demo Generative AI application will use the new model set by this parameter to generate text.


# Steps

Follow the steps below to add the continuous fine-tuning stage to the CI/CD pipeline.

> The fine-tuning process will take about 1.5 hour to complete.

## Update the `constants.py` file

1. In the AWS Management Console, navigate to the `CloudFormation` service.
   
2. Click on the getting started stack `LLMOps-Workshop` created at the beginning of the workshop.
   
3. Select the `Outputs` tab and note down the value for the `SageMakerDomainID` parameter.
   
4. Open the `constants.py` file in the root of the workshop repository.

5. Set the `SAGEMAKER_DOMAIN_ID` variable to be equal to the `SageMakerDomainID` value.

> Given that the FMOps process is automated using a SageMaker Pipeline, all monitoring and management of the pipeline execution occurs within the Amazon SageMaker Studio IDE. By introducing the SageMaker Studio Domain ID as a constant, we grant the SageMaker Execution Role the capability to build, deploy, and oversee the FMOps pipeline.

1. Make sure to save the `constants.py` file.


## Create the `TuningStack`

1. Open the `stacks/tuning.py` file
   
2. For each of the following sections, copy the code into the corresponding section of the `tuning.py` file

Retrieve the pipeline variables from the toolchain context. This loads the fine-tuning parameters, such as Epochs, Batch size, Learning rate, and Learning warmup steps. These parameters are used to tweak the foundation model fine-tuning process.

```python
        context = self.node.try_get_context("toolchain-context")
```

Create an S3 buckets, which will trigger the fine-tuning process when a fine-tuning dataset is uploaded.

```python
        tuning_bucket = _s3.Bucket(
            self,
            "TuningDataBucket",
            bucket_name=f"{self.stack_name.lower()}-{cdk.Aws.REGION}-{cdk.Aws.ACCOUNT_ID}",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True
        )
        cdk.CfnOutput(self, "TuningDataBucketName", value=tuning_bucket.bucket_name)
```

Create an Amazon Bedrock service IAM role that grants Bedrock access permissions to the fine-tuning data in the `tuning_bucket`.

```python
        bedrock_role = _iam.Role(
            self,
            "BedrockServiceRole",
            assumed_by=_iam.ServicePrincipal(
                service="bedrock.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "aws:SourceAccount": cdk.Aws.ACCOUNT_ID
                    },
                    "ArnEquals": {
                        "aws:SourceArn": f"arn:{cdk.Aws.PARTITION}:bedrock:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:model-customization-job/*"
                    }
                }
            ),
            inline_policies={
                "BedrockS3Policy": _iam.PolicyDocument(
                    statements=[
                        _iam.PolicyStatement(
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:ListBucket"
                            ],
                            effect=_iam.Effect.ALLOW,
                            resources=[
                                f"arn:{cdk.Aws.PARTITION}:s3:::{tuning_bucket.bucket_name}",
                                f"arn:{cdk.Aws.PARTITION}:s3:::{tuning_bucket.bucket_name}/*"
                            ],
                            conditions={
                                "StringEquals": {
                                    "aws:PrincipalAccount": cdk.Aws.ACCOUNT_ID
                                }
                            }
                        )
                    ]
                )
            }
        )
```

Define the SQS callback queue that integrates the fine-tuning workflow with the SageMaker Pipeline. As mentioned earlier, there is currently no direct integration between a SageMaker Pipeline and Bedrock. The SQS queue acts as the bridge between the SageMaker Pipeline and the Bedrock fine-tuning jobs.

```python
        callback_queue = _sqs.Queue(
            self,
            "CallbackQueue",
            visibility_timeout=cdk.Duration.seconds(120)
        )
```

Add the fine-tuning handler, using the pre-defined `FineTuner` component. This component consists of a Lambda function that creates a Bedrock fine-tuning job to customize the foundation model. The Lambda function also monitors the status of the fine-tuning job, and reports the status back to the SageMaker Pipeline.

```python
        fine_tuner = FineTuner(self, "FineTuner")
```

With the fine-tuning handler defined, we now add the Bedrock service role as an environment variable. This allows the Lambda function to assume the Bedrock service role when starting, and monitoring the fine-tuning job.

```python
        fine_tuner.fine_tuner_handler.add_environment(key="BEDROCK_ROLE", value=bedrock_role.role_arn)
```

Next, create the fine-tuning workflow, using the pre-defined `FineTuningWorkflow` component. This component is an AWS Step Functions State Machine that coordinates the fine-tuning handler.

```python
        FineTuningWorkflow(
            self,
            "TuningWorkflow",
            tuner=fine_tuner.fine_tuner_handler,
            sqs_queue=callback_queue
        )
```

The Step Functions State Machine is illustrated below. The state machine leverages the fine-tuning handler to start a Bedrock fine-tuning job. After a 10-minute wait period, the state machine invokes the fine-tuning handler to verify the status of the running fine-tuning job. If the status indicates that the fine-tuning job is `InProgress`, the workflow waits another 10 minutes before checking the status again. Once the status shows that the fine-tuning job is `Complete`, the workflow reports a `Success` state back to the SageMaker pipeline. Should the fine-tuning job fail, or be manually terminated, the workflow reports a `Failure` state back to the SageMaker pipeline.

![](../img/orchestration-step-function.png)

Next, you add the FMOps pipeline, using the pre-defined `Pipeline` component. This component is an Amazon SageMaker Pipeline that is triggered once fine-tuning data is uploaded to the S3 bucket.

```python
        fmops_pipeline = Pipeline(
            self,
            "FMOpsPipeline",
            data_bucket=tuning_bucket,
            sqs_queue=callback_queue
        )
```

In the above code, the `tuning_bucket` and `callback_queue` are specified as arguments, linking the FMOps pipeline to the data S3 bucket, and the Bedrock fine-tuning job using the SQS queue, by means of a SageMaker Pipeline Callback step. The following image shows what the FMOps pipeline looks like in the Amazon SageMaker Studio IDE:

![](../img/fmops-pipeline.png)

The pipeline is structured as a directed acyclic graph (DAG), detailing each step of the pipeline along with the relationships between them. The data dependencies are encoded between each step, where the properties of a step's output are passed as inputs to the next step. Each step is described below:

1. The `DataPreprocessing` step of the FMOps pipeline runs a SageMaker Processing job to read the fine-tuning data and split it into separate training and validation datasets. Once these datasets are created and stored in the tuning bucket, these data dependencies are passed onto the `FineTuning` step.

2. `FineTuning` is a Callback step to start the fine-tuning workflow. If the model customization process is successfully completed, the validation metric data dependencies are passed onto the `ModelEvaluation` step.

3. `ModelEvaluation` executes another processing job to extract, and store these metrics as metadata.

4. `RegisterModel` stores the model customization metadata for the model version, as model package in the SageMaker Model Registry. As you will learn later in this chapter, having a model version allows the Data Scientist, or ML Practitioner to review the model metrics, assess its quality, purchase Provisioned Throughput, and approve (or deny) the model version for production.

> The SageMaker Pipeline definition for the FMOps pipeline has been codified as a CDK construct using the Pipelines SDK , and can be reviewed in the `/components/fmops_pipeline/pipeline.py` file.

With the pre-defined components declared, we can add the toolchain context variables - as Pipeline parameters  - to initialize the FMOps process.

```python
        fmops_pipeline.start_pipeline_function.add_environment(key="BASE_MODEL", value=context.get("tuning-bedrock-base-model"))
        fmops_pipeline.start_pipeline_function.add_environment(key="EPOCHS", value=context.get("tuning-epoch-count"))
        fmops_pipeline.start_pipeline_function.add_environment(key="BATCHES", value=context.get("tuning-batch-size"))
        fmops_pipeline.start_pipeline_function.add_environment(key="LEARNING_RATE", value=context.get("tuning-learning-rate"))
        fmops_pipeline.start_pipeline_function.add_environment(key="WARMUP_STEPS", value=context.get("tuning-warmup-steps"))
```

Next, you initialize the model approval event handler that will trigger the CI/CD pipeline. This enables the CI/CD pipeline to automatically redeploy the demo Generative AI application and its infrastructure into production environment, once the ML practitioners have approved the fine-tuned model.

```python
        fmops_pipeline.deploy_model_function.add_environment(key="PIPELINE_NAME", value=pipeline_name)
        fmops_pipeline.deploy_model_function.add_environment(key="MODEL_PARAMETER", value=model_parameter)
        fmops_pipeline.deploy_model_function.add_to_role_policy(
            statement=_iam.PolicyStatement(
                sid="ModelParameterAccess",
                actions=["ssm:PutParameter"],
                effect=_iam.Effect.ALLOW,
                resources=[
                    f"arn:{cdk.Aws.PARTITION}:ssm:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:parameter/{model_parameter}"
                ]
            )
        )
        fmops_pipeline.deploy_model_function.add_to_role_policy(
            statement=_iam.PolicyStatement(
                sid="CodePipelineAccess",
                actions=["codepipeline:StartPipelineExecution"],
                effect=_iam.Effect.ALLOW,
                resources=[
                    f"arn:{cdk.Aws.PARTITION}:codepipeline:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:{pipeline_name}"
                ]
            )
        )
```

1. Make sure to save the `tuning.py` file. After all additions, the `TuningStack` class should look like this:

![](../img/tuning-stack.png)
![](../img/tuning-stack-2.png)


## Add the Tuning Stage to the `ToolChainStack`

1. Open the `stacks/toolchain.py` file.

2. Copy the following code into the corresponding section:

```python
        ToolChainStack._add_stage(
            pipeline=pipeline,
            stage_name="TUNING",
            stage_account=self.account,
            stage_region=self.region,
            model_parameter_name="CustomModelName"
        )
```

3. Save the `toolchain.py` file.

4. Commit and push the change to CodeCommit.

```python
git add -A
git commit -m "ci: add continuous tuning stage"
git push ccm main
```

5. In the AWS Management console, search for, and open the `CodePipeline` service console. Select the workshop Pipeline.

6. Wait for the pipeline to execute, and after the `UpdatePipeline` stage has executed, you'll notice that the pipeline has self-mutated, and the `Tuning` stage has been added at the end.


## Fine-tune the foundation model

1. Take a look at the fine-tuning data set at `tuning-data/data.jsonl`.
   
The provided dataset is a sample of the `cnn_dailymail` dataset, available from [Hugging Face](https://huggingface.co/datasets/cnn_dailymail), and released under the Apache-2.0 License.

2. Upload the dataset to the data S3 bucket, with the following command, to trigger the fine-tuning process:

```shell
export WORKLOAD=$(python -c "import constants; print(constants.WORKLOAD_NAME.lower())")
export BUCKET=s3://$WORKLOAD-tuning-$AWS_REGION-$AWS_ACCOUNT_ID
aws s3 sync ./tuning-data $BUCKET/raw-data/
```

You may also use the AWS Management Console to upload the dataset to the S3 bucket.

3. Using the AWS Management console, search for, and click on the `Amazon SageMaker` service. Using the navigation panel on the left-hand side, click on `Studio`.

4. Ensure that the `Select user profile` value is set to `sagemakeruser`, and click on `Open Studio`.

5. Once the SageMaker Studio IDE has launched, on the left-hand navigation panel select `Pipelines` and then click on the `<WORKLOAD-NAME>-FMOpsPipeline` pipeline, and click on the most up to date `Execution` to view the execution graph.

6. Wait for the FMOps pipeline to finish.

> The FMOps pipeline execution should take approximately 1.5 hour to complete.

When it completes, the pipeline will look like this:

![](../img/completed-fmops-pipeline.png)

The `DataPreprocessing` step of the FMOps pipeline runs a SageMaker Processing job to take the sample fine-tuning dataset that was uploaded to S3, and split it into a train and a validation set. The Processing job then stores these datasets in the tuning S3 bucket.

> Each of these datasets has only a single sample. This has been done to speed up the fine-tuning process and save time during the workshop. The runtime logic to run this pre-processing task can be viewed in the `/components/fmops_pipeline/scripts/preprocessing.py` file.

The `FineTuning` step uses SQS to send a message to the Step Functions State Machine which orchestrates the Bedrock model fine-tuning job, using the train and validation datasets from the `DataPreprocessing` step. The execution of the Step Function State Machine can be viewed by searching for and clicking on the `Step Functions` service console. When completes, the execution for the `FineTuningWorkflow` will look as follows:

![](../img/running-orchestration-step-functions.png)

> You can also see the Bedrock fine-tuning job, by searching for `Amazon Bedrock` in the AWS console. Once the Bedrock console is open, use the left-hand navigation panel to select `Custom models`. For details about the training job, select the `Training jobs` tab on the Custom Models page.

The `ModelEvaluation` step of the FMOps pipeline opens the `validation_metrics.csv` file, which is an output from the `FineTuning` step, and reads the Perplexity score for the fine-tuned model on the validation dataset. This metric, along with the validation Loss metric are stored in the tuning S3 bucket.

> The Perplexity score is an objective evaluation metric to determine how well the model predicts the next token sequence on the validation dataset. Lower values indicate a more accurate model.

The final step of the FMOps pipeline is the `RegisterModel` step. This step captures the validation metric output from the `ModelEvaluation` step and stores these as metadata in the SageMaker Model Registry.

It is at this point that the ML Practitioner views the perplexity score of the model version, and assess the custom model's performance against the key performance indicators for the use case. If the model meets the production criteria, the ML Practitioner can perform one or more of the following tasks:

- Purchase [Provisioned Throughput](https://docs.aws.amazon.com/bedrock/latest/userguide/prov-throughput.html) for the model version.
- Manually perform use case specific prompt tests against the model version.
- Execute automated prompt tests against the model version, using the test dataset.
- Perform robust model evaluation of the custom version to ascertain use case specific performance criteria. For example, if the output is unstructured (such as a summary), they can use similarity metrics like Recall-oriented Understudy for Gisting Evaluation [ROUGE](https://en.wikipedia.org/wiki/ROUGE_(metric)), and cosine similarity. See [Model evaluation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-evaluation.html) for more information on how Bedrock support model evaluation jobs.

Once the model version has been deemed suitable for production, it can be manually approved.


## Approve the fine-tuned model for production

1. To approve a model for production, use the SageMaker Studio IDE, navigate to the `Models` menu option in the left-hand navigation panel, and select the `Registered models` tab.

2. Click the `<WORKLOAD NAME>-PackageGroup` group, and select the latest version of the model package.

3. Use the `Actions` button, in the top-right, select the `Update model status` option from the drop-down.

4. In the `Update model status` dialog window, Change the `Status` value to `Approved` option, provide an optional comment for approval, and then click the `Save and update` button.

5. Navigate to `CodePipeline` service in the AWS console. Select the CI/CD pipeline and confirm that a new release in in progress. The release will re-deploy the demo Generative AI application and tell it to use the new fine-tuned model.

# Next steps

Navigate to [Retrieval augmented generation (RAG)](/part-02/80-retrieval-augmented-generation.md) to implement the retrieval augmented generation feature.
