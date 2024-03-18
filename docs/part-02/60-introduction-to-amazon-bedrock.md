# Introduction to Amazon Bedrock

Amazon Bedrock is a fully managed AWS service that offers a choice of high-performing foundation models (FMs) from leading AI companies like AI21 Labs, Anthropic, Cohere, Meta, Mistral AI, Stability AI, and Amazon via a single API. Using Amazon Bedrock, you can experiment with and evaluate top FMs for your use case, privately customize them with your data using techniques such as fine-tuning and Retrieval Augmented Generation (RAG). Since Amazon Bedrock is serverless, you don't have to manage any infrastructure, and you can securely integrate and deploy generative AI capabilities into your applications using the AWS services you are already familiar with.

<iframe width="584" height="329" src="https://www.youtube.com/embed/_vdK5PgcNvc" title="Introducing Amazon Bedrock | Amazon Web Services" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

[Learn more about Amazon Bedrock here](https://aws.amazon.com/bedrock/)

# How Amazon Bedrock is utilized in this workshop

The demo application in this workshop relies on Amazon Bedrock to get access to below LLMs:
- Anthropic Claude Instant
- Anthropic Claude Sonnet
- Stability AI Stable Diffusion XL 1.0
- Amazon Titan Embeddings G1 - Text

The Anthropic Claude Instant and Claude Sonnet models are used to generate text based on the user input in the `Question & Answer` tab. The Stability AI Stable Diffusion XL 1.0 model is used to generate images in `Generate Image` tab. The Amazon Titan Embeddings G1 - Text model is used to generate embeddings from user input if RAG is enabled in the `Question & Answer` tab, and to convert context text data to embeddings during vector database hydration.

# Evaluate foundation models with Amazon Bedrock

You may evaluate the foundation models available in Amazon Bedrock by using its `Playgrounds` feature. It is especially useful when you need to understand the capabilities of the models or to develop your prompts.

Follow below steps to access Amazon Bedrock `Playgrounds` feature:

1. In the AWS Management console, search for and navigate to the `Amazon Bedrock` service.
2. In the navigation pane, under `Playgrounds`, choose either `Chat`, `Text` or `Image` based on the type of foundation model you want to evaluate.
3. Click on `Select Model` to choose the specific model you want to evaluate.
4. Enter your prompt and optional configurations and observe the model's response.

# Next Steps

Navigate to [Continuous fine-tuning](/part-02/70-continuous-fine-tuning.md) to implement the continuous fine-tuning process for the demo application.
