# Clean Up

Congratulations, you have completed the workshop!

You may now clean up the resources created in this workshop to avoid incurring any additional costs.

## Delete the CloudFormation Stacks

Now you will clean up the resources created in this workshop.

1. Search `CloudFormation` in the AWS Console.

2. Individually select and delete the following stacks in order. Wait for the status on the deleted stack to return `DELETE_COMPLETE`, before moving onto deleting the next stack.

   - `LLMOps-Workshop-TUNING`
   - `LLMOps-Workshop-PROD`
   - `LLMOps-Workshop-QA`
   - `LLMOps-Workshop-Toolchain`
   - `LLMOps-Workshop` (getting started stack, the name may be different if you modified it at the beginning of the workshop)

Deletion of all stacks will take between 10-20 minutes to complete.

> Do not delete the `CDKToolkit` stack. This stack is created by the AWS CDK and is used by the CDK to manage resources. Deleting this stack will prevent you from deleting other stacks in the future. 
> You may only delete the `CDKToolkit` stack after you have deleted all other stacks created in the workshop.
  
3. Delete the fine-tuned Bedrock model.

   - In the AWS Management Console, navigate to the Amazon Bedrock service.
   - Under `Foundation Models`, select `Custom models`.
   - Under `Models` tab, select the model you fine-tuned in the workshop.
   - Click `Delete` in the action menu and confirm the deletion.
