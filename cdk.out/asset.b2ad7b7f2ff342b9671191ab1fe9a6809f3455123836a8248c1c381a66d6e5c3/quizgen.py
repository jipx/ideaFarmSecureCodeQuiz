import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
TABLE_NAME = os.environ.get("SESSION_TABLE")
AGENT_ID = os.environ.get("AGENT_ID")
AGENT_ALIAS_ID = os.environ.get("AGENT_ALIAS_ID")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")

def call_bedrock_agent(category):
    session_id = f"quizgen-{category.lower().replace(' ', '-')}"
    user_input = f"Generate a multiple-choice quiz with hints and explanation for OWASP topic: {category}."
    print(f"[DEBUG] Calling agent with session_id={session_id} and input={user_input}")

    response_stream = bedrock_agent_runtime.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_id,
        inputText=user_input
    )

    response_text = ""
    for event in response_stream["completion"]:
        print(f"[DEBUG] Agent stream event: {event}")
        if "chunk" in event:
            chunk_bytes = event["chunk"].get("bytes")
            if chunk_bytes:
                response_text += chunk_bytes.decode("utf-8")

    print(f"[DEBUG] Raw response text: {response_text}")

    try:
        quiz_data = json.loads(response_text)
        print(f"[DEBUG] Parsed quiz data: {quiz_data}")
        return quiz_data
    except json.JSONDecodeError:
        print("Error decoding agent response:", response_text)
        return {
            "questions": [],
            "error": "Malformed agent response"
        }

def lambda_handler(event, context):
    try:
        print(f"[DEBUG] Incoming event: {event}")
        for record in event["Records"]:
            message = json.loads(record["body"])
            session_id = message["sessionId"]
            category = message["category"]
            print(f"[DEBUG] Processing session_id={session_id}, category={category}")

            quiz_data = call_bedrock_agent(category)
            timestamp = datetime.utcnow().isoformat()

            table = dynamodb.Table(TABLE_NAME)
            table.update_item(
                Key={"sessionId": session_id},
                UpdateExpression="SET #s = :s, #q = :q, updatedAt = :t",
                ExpressionAttributeNames={
                    "#s": "status",
                    "#q": "quiz"
                },
                ExpressionAttributeValues={
                    ":s": "completed",
                    ":q": quiz_data,
                    ":t": timestamp
                }
            )
            print(f"[DEBUG] Updated DynamoDB for session_id={session_id}")

    except Exception as e:
        print("[ERROR] Exception in quizgen lambda_handler:", str(e))
        raise