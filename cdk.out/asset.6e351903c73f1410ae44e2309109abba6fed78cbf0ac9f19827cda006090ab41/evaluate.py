import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get("SESSION_TABLE")

def lambda_handler(event, context):
    for record in event["Records"]:
        payload = json.loads(record["body"])
        session_id = payload.get("sessionId")
        answers = payload.get("answers", [])

        # Dummy score based on answer count
        score = len([a for a in answers if a]) * 10

        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="SET #eval = :val",
            ExpressionAttributeNames={"#eval": "evaluation"},
            ExpressionAttributeValues={":val": {"score": score, "total": len(answers)}}
        )