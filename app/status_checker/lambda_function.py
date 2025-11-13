import boto3
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("GetStatus function invoked")
    logger.info(f"Event: {json.dumps(event)}")

    try:
        # Parametre isim farklarını yakala
        params = event.get("queryStringParameters", {}) or {}
        request_id = (
            params.get("requestId") or
            params.get("request_ID") or
            params.get("request_id")
        )
        if not request_id:
            return response(400, {"error": "Missing requestId"})


        # DynamoDB erişimi
        table_name = os.environ.get("TABLE_NAME", "TranslationStatus-417404104136-cf")
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)

        response_data = table.get_item(Key={"request_ID": request_id})
        item = response_data.get("Item")

        if not item:
            return response(404, {"error": "Request not found"})

        body = {
            "status": item.get("status"),
            "translated_text": item.get("translated_text", ""),
            "download_url": item.get("presigned_url", "")
        }

        return response(200, body)

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return response(500, {"error": str(e)})


def response(status_code, body):
    """Consistent CORS-enabled responses."""
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS"
        },
        "body": json.dumps(body)
    }
