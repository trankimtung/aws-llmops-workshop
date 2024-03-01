## Getting started

Before you begin, you'll need to set up your development environment and deploy the necessary AWS resources that will be utilized later in the workshop. This section will guide you through that process.

## Pre-requisites

- AWS account with AdminstratorAccess
- Computer with internet connection
- A modern web browser
- Visual Studio Code
- Docker


## Setup your environment


> __NOTE:__ It's recommended that you attempt the workshop in a development container, using the provided configuration. 
> 
> Follow these links to learn more about [Development Container](https://containers.dev/) and [Developing inside a container with Visual Studio Code](https://code.visualstudio.com/docs/devcontainers/containers).
>
> Skip this step if you are using development container.

1. Ensure that you have the necessary dependencies installed.
    - Docker
    - Python 3.11
    - Npm
    - AWS CDK 2.128.0
    - AWS CLI 2.15.21

2. Manually create a Python virtualenv:

```shell
python3 -m venv .venv
```

3. After the init process completes, use the following step to activate your virtualenv.

```shell
source .venv/bin/activate
```

4. Once the virtualenv is activated, you can install the required dependencies.

```shell
pip install -r requirements.txt
```


## Setting up your AWS account

Make sure you have your AWS credentials properly configured in your terminal.

If you have an  AWS access key, export it as environment variables by running the following commands in your terminal.

```shell
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Deploy necessary AWS resouces

Choose an AWS Region to deploy resouces into. `us-east-1` is recommended for this workshop.

Click below link to launch the `LLMOps-Workshop` CloudFormation stack into the corresponding AWS Region.

Region|Launch URL
:--|:--
us-east-1|[Launch](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=LLMOps-Workshop&templateURL=https://raw.githubusercontent.com/trankimtung/aws-llmops-workshop/main/getting-started.yml)

Specify an unique stack name, or stick with the default option of `LLMOps-Workshop`. Keep all other settings in the `Specify stack details` section at their default values.

![](img/cf-provide-stack-name.png)

Tick the box to acknowledge that CloudFormation may generate IAM resources in your account, then click `Submit`.

![](img/cf-iam-capability.png)

Alternatively, you can run the following command in your terminal. Before executing this command, ensure your AWS credentials are properly configured.

```shell
aws cloudformation create-stack --stack-name LLMOps-Workshop --capabilities CAPABILITY_IAM --template-body file://getting-started.yml
```

> The deployment will take about 20 minutes to complete. You can monitor the progress under the `Events` tab within your CloudFormation Stack.

Once the status changes to `CREATE_COMPLETE`, you'll know that the stack has been successfully launched.


### Request access to Amazon Bedrock foundation models

1. In the Management Console, search for `Amazon Bedrock`, and using the left-hand navigation panel, scroll down to select `Model Access`.

2. In the `Model access` panel, click the `Manage model access` button, in the top right-hand corner.

3. Select the check-box for Anthropic, and click the `Submit use case details` button. Fill out the use case form.

4. Click the `Submit` button.

> The base model access approval process for Stability AI, and Anthropic should take approximately 10 minutes to process.

5. Check the boxes for these models:
   -  `Titan Embeddings G1 - Text`
   -  `Titan Text G1 - Express`
   -  `Claude Instant`
   -  `SDXL 1.0`

6. Click the `Save changes` button to submit the license approval process.



## Summary

In this section, you have set up your development environment and deploy the AWS resources necessary for the workshop into your AWS accounts. These resources include a SageMaker Domain, an OpenSearch cluster, IAM roles, and more. You also submitted a request to gain access to the essential Amazon Bedrock foundation models.

[Click here to proceed to the next section.](/.docs/part-1/10-writing-application-and-infrastructure.md)
