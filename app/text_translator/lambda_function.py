import boto3
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("TextTranslator function started")
    logger.info(f"Event received: {json.dumps(event)}")

    try:
        translate = boto3.client('translate')
        s3 = boto3.client('s3')
        dynamodb = boto3.resource('dynamodb')

        table_name = os.environ.get('TABLE_NAME', 'TranslationStatus-417404104136-cf')
        bucket_name = os.environ.get('BUCKET_NAME', 'pdf-translations-417404104136-cf')

        record = event['Records'][0]
        message = json.loads(record['body'])
        logger.info(f"Processing request_ID: {message.get('request_ID')}")

        # .pdf uzantısını kaldır
        request_id = message['request_ID']

        # === DynamoDB’den dil bilgilerini al ===
        table = dynamodb.Table(table_name)
        response = table.get_item(Key={'request_ID': request_id})
        item = response.get('Item', {})

        if not item:
            raise Exception(f"No record found in DynamoDB for request_ID: {request_id}")

        from_lang = item.get('fromLang', 'auto')
        to_lang = item.get('toLang', 'en')
        logger.info(f"Translating from {from_lang} to {to_lang}")

        # === Çeviri ===
        result = translate.translate_text(
            Text=message['text'],
            SourceLanguageCode=from_lang,
            TargetLanguageCode=to_lang
        )
        translated_text = result['TranslatedText']
        logger.info("Translation completed successfully")

        # === Çeviriyi TXT olarak kaydet ===
        output_key = f"translated_{request_id}.txt"
        s3.put_object(
            Bucket=bucket_name,
            Key=output_key,
            Body=translated_text.encode('utf-8'),
            ContentType="text/plain; charset=utf-8"
        )
        logger.info(f"Translated text saved to S3: s3://{bucket_name}/{output_key}")

        # === Presigned URL oluştur (TXT dosyası için) ===
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': output_key},
            ExpiresIn=3600  # 1 saat geçerli
        )
        logger.info(f"Generated presigned URL: {presigned_url}")

        # === DynamoDB kaydını güncelle ===
        table.update_item(
            Key={'request_ID': request_id},
            UpdateExpression="SET #status = :status, translated_text = :text, presigned_url = :url",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'COMPLETED',
                ':text': translated_text,
                ':url': presigned_url
            }
        )
        logger.info("DynamoDB updated successfully")

        return {
            'status': 'COMPLETED',
            'download_url': presigned_url
        }

    except Exception as e:
        logger.error(f"Error in translation: {str(e)}", exc_info=True)
        raise e
