# nOps cli Configuration and Script Management Script - Proof of Concept

This Python script utilizes the [AWS Bedrock](https://aws.amazon.com/bedrock/) service to assist with tasks related to configuration files and scripts. It uses the Boto3 library to interact with a Bedrock model (e.g., `amazon.nova-pro-v1:0`) to generate, edit, or explain files like YAML, JSON, XML, Dockerfiles, and shell scripts. This tool is ideal for DevOps engineers and requires specific setup in your AWS environment to function correctly. It uses Bedrock Foundation Model LLMs directly instead of via the agents because I was runing into issues where LLM prompts Would get confusted when you add agent instructions to focus the output and sometimes it would try to use files / paths local to the agent to fill the request. I'll keep messing with it ad see if i can get clean output from the agent as its a better structure for a production tool. You can read about the prepovisioning limitations [here](https://the-decoder.com/aws-reportedly-faces-customer-frustration-over-anthropic-usage-limits/): 

**nops_cli.py**

Prerequisites

To use this script, ensure the following are set up on your local machine and AWS environment:

1\. AWS Account and Credentials

*   AWS Account: You need an active AWS account with access to the Bedrock service.
    
*   AWS CLI: Install the AWS Command Line Interface (CLI) and configure it with your credentials.
    
    *   Install the AWS CLI: [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
        
    *   Configure it by running:
        
            aws configure
        
        Provide your AWS Access Key ID, Secret Access Key, region (e.g., `us-east-1`), and output format (e.g., json).
        
*   Credentials: Ensure your AWS credentials have the required IAM permissions (see IAM Permissions below).
    

2\. Python and Dependencies

*   Python 3.6+: Install Python on your system if it’s not already present. Verify with:
    
        python3 --version
    
*   Boto3: Install the Boto3 library, which allows the script to communicate with AWS services.
    
        pip install boto3
    

3\. AWS Bedrock Setup

*   Bedrock Model Access: Confirm that the Bedrock model you plan to use (e.g., `amazon.nova-pro-v1:0`) is available in your AWS region. **NOTE**: The Anthropic Models like **Claude 3.5 Haiku** and **Claude 3.7 Sonnet** work best for code but because of some limitations and the need to preprovision usage been testing with Amazon Nova Pro. it seems to work well enough for a prototype. 
    
    *   List available models with:
        
            aws bedrock list-foundation-models --region <your-region>
        
    *   Replace <your-region> with your AWS region (e.g., `us-east-1`).
    *   You can get more details on what models are in each region [here](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html)
        
*   Provisioned Throughput (Optional, skip if using amazon models): Some Bedrock models (like Anhropic) require provisioned throughput for consistent performance. If needed, set it up:
    
        aws bedrock create-provisioned-model-throughput \
            --model-id <model-id> \
            --provisioned-model-name my-model \
            --commitment-duration P1D \
            --region <your-region>
    
    *   Replace <model-id> with your chosen model ID (e.g., `amazon.nova-pro-v1:0`).
        
    *   Note the `provisionedModelArn` returned by this command and use it in the script instead of the `modelId`.
        

IAM Permissions

The AWS credentials used by the script must be associated with an IAM user or role that has the following permissions:

*   `bedrock:InvokeModel`: Required to call the Bedrock model.
    
*   `bedrock:CreateProvisionedModelThroughput` and `bedrock:ListProvisionedModelThroughputs` (optional, only if using provisioned throughput).
    

Here’s an example IAM policy to attach to your user or role:

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:CreateProvisionedModelThroughput",
                    "bedrock:ListProvisionedModelThroughputs"
                ],
                "Resource": "*"
            }
        ]
    }

*   Attach this policy via the AWS Management Console or CLI:
    
        aws iam attach-user-policy --user-name <your-iam-user> --policy-arn arn:aws:iam::aws:policy/<your-policy-name>
    

Script Configuration

Before running the script, configure the following:

*   Model ID: In the script, set the modelId variable to the Bedrock model you’re using (e.g., `amazon.nova-pro-v1:0`).
    
*   Region: In the Boto3 client initialization, set region\_name to your AWS region (e.g., `us-east-1`).
    

Example Boto3 client setup in the python script:

    # Create a Boto3 client and invoke the model
    try:
        client = boto3.client('bedrock-runtime', region_name='us-east-1')
        response = client.invoke_model(
            modelId='amazon.nova-pro-v1:0',  # Replace with your desired model ID

You will also need to configure the body based on the requirements of the model. you can find the body requirement in the api example in the [model explorer](https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/model-catalog/serverless/amazon.nova-pro-v1:0).

Usage

Run the script from the command line with the following arguments:

*   `--prompt`: (Required) Your request (e.g., "Generate a YAML file for a Kubernetes pod").
    
*   `--file`: (Optional) Path to an existing file to analyze or edit.
    
*   `--diff`: (Optional) Show differences when editing a file.
    

Examples

1.  Generate a New File:
    
        python nops_cli.py --prompt "Generate a basic Nginx configuration file."
    
    Output: Saved as config\_<timestamp>.conf (e.g., `config_241023153045.conf`).
    
2.  Explain a File:

        python nops_cli.py --prompt "Explain this file." --file docker-compose.yml
    
    Output: Explanation printed to the console.
    
3.  Edit a File:
    
        python nops_cli.py --prompt "Add a new service named 'db'." --file docker-compose.yml --diff
    
    Output: Saved as docker-compose\_edited\_<timestamp>.yml, with differences displayed.
    

Additional Notes

*   File Safety: Edited files are saved with timestamps to avoid overwriting originals.
    
*   ***Cleanup***: If you set up provisioned throughput, delete it when finished to avoid unnecessary costs:
    
        aws bedrock delete-provisioned-model-throughput --provisioned-model-id <arn> --region <your-region>
    

For further assistance, consult the [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/).

* * *

