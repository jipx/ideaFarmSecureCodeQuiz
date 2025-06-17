import json
import os
import boto3
import uuid
import re
from datetime import datetime

# AWS clients
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

# Environment variables
TABLE_NAME = os.environ.get("SESSION_TABLE")
QUIZGEN_QUEUE_URL = os.environ.get("QUIZGEN_QUEUE_URL")

# Allowed values
ALLOWED_DIFFICULTIES = {"low", "medium", "high"}
ALLOWED_CATEGORIES = {
    "SQL Injection", "XSS", "Broken Authentication", "Sensitive Data Exposure",
    "Security Misconfiguration", "Insecure Deserialization",
    "Using Components with Known Vulnerabilities", "Broken Access Control",
    "Insufficient Logging & Monitoring", "Server-Side Request Forgery"
}

def lambda_handler(event, context):
    try:
        # Parse input
        body = json.loads(event.get("body", "{}"))
        user_id = body.get("userId", "").strip()
        category = body.get("category", "").strip()
        difficulty = body.get("difficulty", "medium").lower().strip()

        # --- Validate userId ---
        if not user_id or not re.match(r"^[a-zA-Z0-9_\-]{3,30}$", user_id):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid or missing userId"})
            }

        # --- Validate category ---
        if category not in ALLOWED_CATEGORIES:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"Invalid category. Allowed: {sorted(list(ALLOWED_CATEGORIES))}"
                })
            }

        # --- Validate difficulty ---
        if difficulty not in ALLOWED_DIFFICULTIES:
            difficulty = "medium"  # fallback

        # Generate session ID and timestamp
        session_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # --- Store in DynamoDB ---
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item={
            "sessionId": session_id,
            "userId": user_id,
            "category": category,
            "difficulty": difficulty,
            "status": "pending",
            "createdAt": timestamp
        })

        # --- Send only to QuizGen queue ---
        payload = {
            "sessionId": session_id,
            "userId": user_id,
            "category": category,
            "difficulty": difficulty
        }

        sqs.send_message(
            QueueUrl=QUIZGEN_QUEUE_URL,
            MessageBody=json.dumps(payload)
        )

        # --- Return success ---
        return {
            "statusCode": 200,
            "body": json.dumps({"sessionId": session_id})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
