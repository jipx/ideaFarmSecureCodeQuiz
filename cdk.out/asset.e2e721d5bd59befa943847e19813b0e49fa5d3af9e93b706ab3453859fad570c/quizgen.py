import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
TABLE_NAME = os.environ.get("SESSION_TABLE")
AGENT_ID = os.environ.get("AGENT_ID")
AGENT_ALIAS_ID = os.environ.get("AGENT_ALIAS_ID")  # if versioning is used
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")

def call_bedrock_agent(category):
    session_state = {
        "sessionId": f"quizgen-{category.lower().replace(' ', '-')}",
        "enableTrace": False
    }
    user_input = f"Generate a multiple-choice quiz with hints and explanation for OWASP topic: {category}."

    response = bedrock_agent_runtime.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_state["sessionId"],
        inputText=user_input
        
    )

    # The agent's response body is a byte stream
    response_body = response['completion']['content']
    return json.loads(response_body)

def lambda_handler(event, context):
    try:
        for record in event["Records"]:
            message = json.loads(record["body"])
            session_id = message["sessionId"]
            category = message["category"]

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

    except Exception as e:
        print("Error in quizgen:", str(e))
        raise