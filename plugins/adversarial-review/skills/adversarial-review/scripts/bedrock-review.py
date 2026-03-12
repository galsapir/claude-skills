# /// script
# requires-python = ">=3.10"
# dependencies = ["boto3"]
# ///
# ABOUTME: Sends a review prompt to AWS Bedrock's converse API and prints the response.
# ABOUTME: Used as a backend for the adversarial-review skill.

import argparse
import sys

import boto3


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a review prompt to Bedrock")
    parser.add_argument("prompt_file", help="Path to the prompt markdown file")
    parser.add_argument(
        "--model",
        default="eu.anthropic.claude-sonnet-4-6-v1:0",
        help="Bedrock model ID",
    )
    parser.add_argument("--region", default="eu-west-1", help="AWS region")
    args = parser.parse_args()

    with open(args.prompt_file) as f:
        prompt = f.read()

    if not prompt.strip():
        print("Error: prompt file is empty", file=sys.stderr)
        return 1

    client = boto3.client("bedrock-runtime", region_name=args.region)

    response = client.converse(
        modelId=args.model,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 8192, "temperature": 0.3},
    )

    output_message = response["output"]["message"]
    for block in output_message["content"]:
        if "text" in block:
            print(block["text"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
