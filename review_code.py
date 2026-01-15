import os
import json
import boto3
import urllib.request

GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
GITHUB_REPO = os.environ['GITHUB_REPO']

bedrock = boto3.client("bedrock-runtime")

def fetch_github_code():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/"
    req = urllib.request.Request(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    with urllib.request.urlopen(req) as response:
        files = json.loads(response.read().decode())

    code_files = {}
    for f in files:
        if f['name'].endswith('.py'):
            file_req = urllib.request.Request(f['download_url'])
            with urllib.request.urlopen(file_req) as file_response:
                file_content = file_response.read().decode()
            code_files[f['name']] = file_content
    return code_files

def review_code_with_bedrock(code):
    body = {
        "messages": [
            {"role": "user", "content": f"Review this Python code and provide a simple text-based review:\n{code}"}
        ],
        "max_tokens": 300,
        "anthropic_version": "bedrock-2023-05-31"
    }

    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]

def lambda_handler(event, context):
    code_files = fetch_github_code()
    reviews = {}

    for filename, code in code_files.items():
        reviews[filename] = review_code_with_bedrock(code)

    print("Code Reviews:", json.dumps(reviews, indent=2))
    return {
        "statusCode": 200,
        "body": json.dumps(reviews)
    }

