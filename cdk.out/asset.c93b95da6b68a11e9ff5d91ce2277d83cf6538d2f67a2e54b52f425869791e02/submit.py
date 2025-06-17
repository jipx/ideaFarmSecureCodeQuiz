import json
import os
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

TABLE_NAME = os.environ.get("SESSION_TABLE")
QUIZGEN_QUEUE_URL = os.environ.get("QUIZGEN_QUEUE_URL")
EVALUATION_QUEUE_URL = os.environ.get("EVALUATION_QUEUE_URL")
RECORD_QUEUE_URL = os.environ.get("RECORD_QUEUE_URL")

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        user_id = body.get("userId")
        category = body.get("category")

        if not user_id or not category:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing userId or category"})
            }

        session_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item={
            "sessionId": session_id,
            "userId": user_id,
            "category": category,
            "status": "pending",
            "createdAt": timestamp
        })

        # Dispatch to queues
        payload = {"sessionId": session_id, "userId": user_id, "category": category}
        for queue_url in [QUIZGEN_QUEUE_URL, EVALUATION_QUEUE_URL, RECORD_QUEUE_URL]:
            sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(payload))

        return {
            "statusCode": 200,
            "body": json.dumps({"sessionId": session_id})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }