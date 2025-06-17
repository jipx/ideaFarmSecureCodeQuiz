import json
import os
import boto3
from datetime import datetime

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=os.environ.get("BEDROCK_REGION"))

# Environment variables
TABLE_NAME = os.environ.get("SESSION_TABLE")
AGENT_ID = os.environ.get("AGENT_ID")
AGENT_ALIAS_ID = os.environ.get("AGENT_ALIAS_ID")


# --- Utilities ---

def extract_json_from_response(text):
    """Attempt to extract the first valid JSON object from mixed text."""
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


def get_text_from_stream(response_stream):
    """Extract raw text response from Bedrock streaming response."""
    full_response = ""
    for event in response_stream["completion"]:
        if "chunk" in event and "bytes" in event["chunk"]:
            full_response += event["chunk"]["bytes"].decode("utf-8")
    return full_response


# --- Lambda Handler ---

def lambda_handler(event, context):
    try:
        for record in event["Records"]:
            message = json.loads(record["body"])
            session_id = message["sessionId"]
            category = message["category"]
            difficulty = message.get("difficulty", "medium").lower()

            # Validate difficulty
            allowed_levels = {"low", "medium", "high"}
            if difficulty not in allowed_levels:
                print(f"[WARN] Invalid difficulty '{difficulty}', defaulting to 'medium'")
                difficulty = "medium"

            print(f"[INFO] Generating quiz for category '{category}' at difficulty '{difficulty}'")

            # Construct prompt
            input_text = (
                f"You are a secure coding assistant. Respond only with valid JSON, no explanations.\n"
                f"Generate a multiple choice quiz for the OWASP topic: {category} at {difficulty} difficulty level.\n"
                f"Use this JSON format:\n"
                f"{{\n"
                f'  "questions": [\n'
                f"    {{\n"
                f'      "question": "string",\n'
                f'      "options": ["string", "string", "string", "string"],\n'
                f'      "answer": "string"\n'
                f"    }}\n"
                f"  ]\n"
                f"}}"
            )

            # Invoke agent
            response_stream = bedrock_agent_runtime.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                sessionId=session_id,
                inputText=input_text
            )

            # Parse output
            output = get_text_from_stream(response_stream)
            print("[DEBUG] Raw agent output:", output)
            quiz_data = extract_json_from_response(output)

            if not quiz_data:
                raise ValueError("Malformed agent response: Could not extract valid JSON")

            # Save to DynamoDB
            table = dynamodb.Table(TABLE_NAME)
            timestamp = datetime.utcnow().isoformat()

            table.update_item(
                Key={"sessionId": session_id},
                UpdateExpression="SET #s = :s, #q = :q, #r = :r, #d = :d, updatedAt = :t",
                ExpressionAttributeNames={
                    "#s": "status",
                    "#q": "quiz",
                    "#r": "rawResponse",
                    "#d": "difficulty"
                },
                ExpressionAttributeValues={
                    ":s": "completed",
                    ":q": quiz_data,
                    ":r": output,
                    ":d": difficulty,
                    ":t": timestamp
                }
            )

            print(f"[INFO] Quiz stored successfully for session_id={session_id}")

    except Exception as e:
        print("[ERROR] Exception occurred:", str(e))
        if 'output' in locals():
            print("[ERROR] Raw agent output was:", output)
        raise

