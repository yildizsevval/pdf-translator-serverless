import boto3
import PyPDF2
import io
import json
import logging
import os
import urllib.parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("PDFExtractor function started")
    logger.info(f"Event received: {json.dumps(event)}")
    
    try:
        # Initialize clients
        s3 = boto3.client('s3')
        dynamodb = boto3.resource('dynamodb')
        sqs = boto3.client('sqs')
        
        # Get file details from S3 trigger
        bucket = event['Records'][0]['s3']['bucket']['name']
        #key = event['Records'][0]['s3']['object']['key']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
        logger.info(f"Processing file: s3://{bucket}/{key}")
        
        # 1. Download PDF
        response = s3.get_object(Bucket=bucket, Key=key)
        pdf_file = io.BytesIO(response['Body'].read())
        logger.info("PDF downloaded successfully")

        # 2. Extract text with error handling for invalid PDFs
        table_name = os.environ.get('TABLE_NAME', 'TranslationStatus-417404104136-cf')
        table = dynamodb.Table(table_name)

        try:
            reader = PyPDF2.PdfReader(pdf_file)
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            logger.info(f"Extracted {len(text)} characters from PDF")
        except PyPDF2.errors.PdfReadError as e:
            logger.error(f"Invalid PDF format: {str(e)}")
            table.update_item(
                Key={'request_ID': key},
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'FAILED_INVALID_PDF'}
            )
            return {'status': 'failed'}

        # 3. Update DynamoDB status
        table.update_item(
            Key={'request_ID': key},
            UpdateExpression="SET #status = :status, extracted_text = :text",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'EXTRACTED',
                ':text': text
            }
        )
        logger.info("DynamoDB updated successfully")
        
        # 4. Send message to SQS
        queue_url = os.environ.get('QUEUE_URL')
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({
                'request_ID': key,
                'text': text,
                'bucket': bucket
            })
        )
        logger.info("Message sent to SQS successfully")
        
        return {'status': 'success'}
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        raise e
