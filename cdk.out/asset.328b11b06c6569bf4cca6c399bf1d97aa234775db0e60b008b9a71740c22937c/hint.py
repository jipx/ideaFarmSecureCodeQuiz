import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get("SESSION_TABLE")

def lambda_handler(event, context):
    for record in event["Records"]:
        payload = json.loads(record["body"])
        session_id = payload.get("sessionId")

        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="SET #h = :val",
            ExpressionAttributeNames={"#h": "hintProvided"},
            ExpressionAttributeValues={":val": True}
        )