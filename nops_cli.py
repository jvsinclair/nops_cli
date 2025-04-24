import argparse
import boto3
import json
import re
import os
from datetime import datetime

# Predefined instructions included with every prompt
INSTRUCTIONS = """
You are a DevOps engineer with expertise in configuration files (e.g., YAML, JSON, INI) and scripts (e.g., shell, Python, JavaScript). Your role is to assist users with the following tasks:
- Explaining: Analyze and explain the components, purpose, and key settings of configuration files or scripts.
- Editing: Help users modify existing configuration files or scripts based on their requests.
- Generating: Create new configuration files or scripts from scratch according to the user’s specifications.

If a user’s request strays from these tasks, politely redirect them back to this scope.

To ensure accuracy, if a request is unclear—especially regarding the application, version, or script type—ask follow-up questions like, 'Which application is this configuration file for?' or 'What type of script are you working with?'

When providing a configuration file or script, wrap the content in triple backticks with the appropriate language identifier (e.g., ```xml, ```yaml, ```sh, ```py). Do not include any additional text outside the code block for configuration or script outputs.
"""

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Invoke AWS Bedrock model for configuration and script tasks.")
    parser.add_argument("--prompt", required=True, help="The user's query or request.")
    parser.add_argument("--file", help="Path to the configuration or script file.")
    parser.add_argument("--diff", action="store_true", help="Show diff when editing.")
    args = parser.parse_args()

    # Read the file if provided
    file_content = None
    file_ext = None
    if args.file:
        try:
            with open(args.file, 'r') as f:
                file_content = f.read()
            file_ext = os.path.splitext(args.file)[1][1:]  # Extract extension (e.g., 'xml')
            file_prompt = f"\nHere is the file:\n```{file_ext}\n{file_content}\n```"
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.")
            return
    else:
        file_prompt = ""

    # Construct the full prompt with instructions, user input, and file content (if any)
    full_prompt = INSTRUCTIONS + "\n\n" + args.prompt + file_prompt

    # Prepare the request body for the AWS Bedrock model
    body = {
        "inferenceConfig": {
            "max_new_tokens": 1000
        },
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": full_prompt
                    }
                ]
            }
        ]
    }

    # Create a Boto3 client and invoke the model
    try:
        client = boto3.client('bedrock-runtime', region_name='us-east-1')
        response = client.invoke_model(
            modelId='amazon.nova-pro-v1:0',  # Replace with your desired model ID
            body=json.dumps(body),
            accept='application/json',
            contentType='application/json'
        )
    except Exception as e:
        print(f"Error invoking Bedrock model: {e}")
        return

    # Parse the response from the model
    try:
        response_body = response['body'].read().decode('utf-8')
        response_json = json.loads(response_body)
        generated_text = response_json['output']['message']['content'][0]['text']
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing model response: {e}")
        return

    # Always search for a code block in the response
    code_block_match = re.search(r'```(\w+)?\n(.*?)\n```', generated_text, re.DOTALL)
    if code_block_match:
        # Extract language identifier and content
        lang = code_block_match.group(1) or 'txt'
        content = code_block_match.group(2)

        # Map language identifier to file extension
        extension_map = {
            'xml': 'xml',
            'yaml': 'yaml',
            'yml': 'yaml',
            'json': 'json',
            'ini': 'ini',
            'dockerfile': 'Dockerfile',
            'docker-compose': 'yml',
            'rb': 'rb',
            'tf': 'tf',
            'pp': 'pp',
            'js': 'js',
            'sh': 'sh',
            'py': 'py',
            'txt': 'txt'
        }
        file_ext = extension_map.get(lang.lower(), 'txt')

        # Generate timestamp for the filename
        timestamp = datetime.now().strftime("%y%m%d%H%M%S")

        if args.file:
            # Save edited file with original extension and timestamp
            base_name = os.path.splitext(args.file)[0]
            edited_file = f"{base_name}_edited_{timestamp}.{file_ext}"
            with open(edited_file, 'w') as f:
                f.write(content)
            print(f"Edited file saved to {edited_file}")
            if args.diff:
                # Optional: Show diff
                import difflib
                original_lines = file_content.splitlines()
                edited_lines = content.splitlines()
                diff = difflib.unified_diff(original_lines, edited_lines, fromfile=args.file, tofile=edited_file)
                print("\nDifferences:\n" + "\n".join(diff))
        else:
            # Save generated file with language-based extension and timestamp
            config_file = f"config_{timestamp}.{file_ext}"
            with open(config_file, 'w') as f:
                f.write(content)
            print(f"Generated file saved to {config_file}")
    else:
        # No code block found, print the response as-is
        print(generated_text)

if __name__ == "__main__":
    main()
