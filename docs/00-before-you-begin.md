# Before you begin

To ensure that you have access to all the necessary AWS resources and services, follow the steps below.

> Note: We'll use `us-east-1` as the AWS region for this workshop.   
> Make sure you have set the correct region in the AWS Management Console or in your AWS CLI configuration.

Furthermore, check out the terminology section at the end of this document to understand the terms used in this workshop.

# Request access to Amazon Bedrock foundation models

1. Open the [AWS Management Console](https://console.aws.amazon.com/), search for `Amazon Bedrock`, and using the left-hand navigation panel, scroll down to select `Model Access`.

2. In the `Model access` panel, click the `Manage model access` button, in the top right-hand corner.

3. Select the check-box for __Anthropic__, and click the `Submit use case details` button. Fill out the use case form.

4. Click the `Submit` button.

> The base model access approval process for Stability AI and Anthropic should take approximately 10 minutes to complete.

5. Check the boxes for these models:
   - `Titan Embeddings G1 - Text`
   - `Titan Text G1 - Express`
   - `Claude Instant`
   - `Claude Sonnet`
   - `SDXL 1.0`

6. Click the `Save changes` button to submit the license approval process.


# Request service quota increase for AWS CodeBuild

For new AWS accounts, the default service quotas for AWS CodeBuild may not be sufficient to run the workshop. In particular, the `maximum number of concurrently running builds` for Linux/Small and Linux/Medium environments may need to be increased.

Follow the steps below in AWS Console to request a service quota increase for AWS CodeBuild. If your account already has a sufficient service quota (more than 5), you can skip this section.

1. Open the [AWS Management Console](https://console.aws.amazon.com/).
2. In the search bar, type `Service Quotas` and select the service.
3. In the left-hand navigation pane, select `AWS services`.
4. In the `Service Quotas` dashboard, search and select `AWS CodeBuild` from the list of services.
5. In the `AWS CodeBuild` dashboard, search and select `Concurrently running builds for Linux/Small environment`.
6. Click the `Request increase at account level` button.
7. Set the `Increase quota value` to `5`.
8. Review the request and click the `Request` button.
9. Repeat steps 5-8 for `Concurrently running builds for Linux/Medium environment`.



Alternatively, you can execute the following commands:

```shell
# Maximum number of concurrently running builds for Linux/Small environment
aws service-quotas request-service-quota-increase --service-code codebuild --quota-code L-9D07B6EF --desired-value 5

# Maximum number of concurrently running builds for Linux/Medium environment
aws service-quotas request-service-quota-increase --service-code codebuild --quota-code L-2DC20C30 --desired-value 5
```

# Terminology

__DevOps__ is a set of practices that combines software development (Dev) and IT operations (Ops) to improve collaboration and productivity in delivering software products. It involves automating processes, implementing continuous integration and continuous delivery (CI/CD), and using tools and technologies to streamline the software development lifecycle. DevOps aims to shorten the development cycle, increase deployment frequency, and ensure the stability and reliability of software applications.

__Foundation Models__ are large machine learning models that are pre-trained on vast amounts of data, often terabytes, which can be used natively or serves as the basis for various downstream natural language processing tasks, providing a robust starting point for further fine-tuning and customization to specific applications or domains.

__Foundation Model Operations (FMOps)__ is a term used to describe the methodology and practices for operationalizing Generative AI models, specifically Foundation Models. FMOps builds upon the principles of MLOps (Machine Learning Operations) and adds additional skills, processes, and technologies needed to manage and deploy Foundation Models in production environments. It involves tasks such as model deployment, monitoring, scaling, and maintenance to ensure the efficient and reliable operation of these models.

__Generative AI (GenAI)__ refers to a type of artificial intelligence that has the ability to generate new content, data, or outputs such as text, images, videos, music, and more. It utilizes advanced machine learning models, such as large language models (LLMs) or foundation models, which are pre-trained on vast amounts of data. Generative AI models can understand and generate human-like text across various tasks, including language translation, text summarization, question answering, and more. These models serve as a robust starting point for further fine-tuning and customization to specific applications or domains.

__Large Language Model Operations (LLMOps)__ is a term used to describe the discipline of managing and operationalizing large language models, such as foundation models, in production environments. LLMOps involves the deployment, monitoring, scaling, and maintenance of these models to ensure their efficient and reliable operation. It encompasses practices and technologies from both machine learning operations (MLOps) and natural language processing (NLP) domains.

__Machine Learning Operations (MLOps)__ is the discipline of managing and automating the lifecycle of machine learning models, from development to deployment and maintenance, to ensure their efficient and reliable operation in production environments. MLOps combines principles and practices from software engineering, data engineering, and machine learning to streamline the process of developing and deploying machine learning models. It aims to address the challenges of managing and scaling machine learning models in real-world scenarios.

# Next steps

[Click here to proceed to the next chapter](/00-getting-started.md)