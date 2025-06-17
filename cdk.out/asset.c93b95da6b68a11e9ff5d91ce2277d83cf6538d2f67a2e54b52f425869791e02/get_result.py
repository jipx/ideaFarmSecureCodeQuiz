import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get("SESSION_TABLE")

def lambda_handler(event, context):
    try:
        session_id = event.get("queryStringParameters", {}).get("sessionId")
        if not session_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing sessionId"})}

        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={"sessionId": session_id})
        item = response.get("Item")

        if not item:
            return {"statusCode": 404, "body": json.dumps({"error": "Session not found"})}

        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": item.get("status"),
                "quiz": item.get("quiz", {})
            })
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}