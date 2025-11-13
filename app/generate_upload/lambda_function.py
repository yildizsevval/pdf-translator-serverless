import boto3
import json
import os
import logging
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("GenerateUploadURL function started")
    logger.info(f"Event received: {json.dumps(event)}")

    try:
        s3 = boto3.client(
            's3',
            region_name='eu-west-3',
            endpoint_url='https://s3.eu-west-3.amazonaws.com',
            config=Config(s3={'addressing_style': 'virtual'})
        )
        dynamodb = boto3.client('dynamodb', region_name='eu-west-3')

        bucket_name = os.environ.get('UPLOAD_BUCKET', 'pdf-uploads-417404104136-cf')
        table_name = os.environ.get('TABLE_NAME', 'TranslationStatus-417404104136-cf')

        params = event.get('queryStringParameters') or {}
        from_lang = params.get('fromLang', 'unknown')
        to_lang = params.get('toLang', 'unknown')

        request_id = context.aws_request_id

        # ✅ DOĞRU parametrelerle presigned URL oluştur
        url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': bucket_name, 'Key': request_id},
            ExpiresIn=3600
        )

        # Sadece gerekirse değiştir
        if "s3.amazonaws.com" in url and "s3.eu-west-3.amazonaws.com" not in url:
            url = url.replace("s3.amazonaws.com", "s3.eu-west-3.amazonaws.com")

        # DynamoDB kaydı
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'request_ID': {'S': request_id},
                'fromLang': {'S': from_lang},
                'toLang': {'S': to_lang},
                'status': {'S': 'URLGENERATED'}
            }
        )

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*'
            },
            'body': json.dumps({
                'url': url,
                'request_id': request_id,
                'fromLang': from_lang,
                'toLang': to_lang
            })
        }

    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
