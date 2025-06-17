import json
import os
import boto3
import re
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=os.environ.get("BEDROCK_REGION"))

TABLE_NAME = os.environ.get("SESSION_TABLE")
AGENT_ID = os.environ.get("AGENT_ID")
AGENT_ALIAS_ID = os.environ.get("AGENT_ALIAS_ID")

# Improved JSON extractor using raw_decode
def extract_json_from_response(text):
    try:
        decoder = json.JSONDecoder()
        text = text.strip()
        for i in range(len(text)):
            try:
                result, _ = decoder.raw_decode(text[i:])
                return result
            except json.JSONDecodeError:
                continue
    except Exception as e:
        print("[ERROR] JSON extraction failed:", str(e))
    return None

# Read text from agent streaming response
def get_text_from_stream(response_stream):
    full_response = ""
    for event in response_stream["completion"]:
        if "chunk" in event and "bytes" in event["chunk"]:
            full_response += event["chunk"]["bytes"].decode("utf-8")
    return full_response

def lambda_handler(event, context):
    try:
        for record in event["Records"]:
            message = json.loads(record["body"])
            session_id = message["sessionId"]
            category = message["category"]

            print(f"[INFO] Calling agent for category: {category}")

            response_stream = bedrock_agent_runtime.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                sessionId=session_id,
                inputText=f"Respond only with valid JSON. Generate a multiple choice quiz for {category} in OWASP."
            )

            output = get_text_from_stream(response_stream)
            print("[DEBUG] Agent raw response:", output)

            quiz_data = extract_json_from_response(output)
            if not quiz_data:
                print("[ERROR] Failed to extract JSON from agent response.")
                raise ValueError("Malformed agent response: JSON structure not found")

            timestamp = datetime.utcnow().isoformat()
            table = dynamodb.Table(TABLE_NAME)
            table.update_item(
                Key={"sessionId": session_id},
                UpdateExpression="SET #s = :s, #q = :q, updatedAt = :t",
                ExpressionAttributeNames={"#s": "status", "#q": "quiz"},
                ExpressionAttributeValues={
                    ":s": "completed",
                    ":q": quiz_data,
                    ":t": timestamp
                }
            )
            print(f"[INFO] Updated DynamoDB for session_id={session_id}")

    except Exception as e:
        print("[ERROR] Exception occurred:", str(e))
        if 'output' in locals():
            print("[ERROR] Raw agent output was:", output)
        raise
