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

def extract_json_from_response(text):
    try:
        match = re.search(r'{.*}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except json.JSONDecodeError as e:
        print("Error decoding JSON from agent response:", str(e))
    return None

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
                inputText=f"Generate a multiple choice quiz for {category} in OWASP"
            )

            output = get_text_from_stream(response_stream)
            print("[DEBUG] Agent raw response:", output)

            quiz_data = extract_json_from_response(output)
            if not quiz_data:
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
            print(f"[DEBUG] Updated DynamoDB for session_id={session_id}")

    except Exception as e:
        print("Error in quizgen Lambda:", str(e))
        raise