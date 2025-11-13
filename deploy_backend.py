import os
import subprocess
import boto3

# ===============================
# CONFIGURATION
# ===============================
REGION = "eu-west-3"
S3_BUCKET = "pdftranslator-code-demo-v2"
STACK_NAME = "pdf-translator-stack-v2"
TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), "pdf-translator-template-v2.yml")
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")

# Eşleşme tablosu (zip dosyası -> CloudFormation'daki S3Key)
ZIP_TO_S3KEY = {
    "generate_upload.zip": "lambda/GenerateUploadURL.zip",
    "pdf_extractor.zip": "lambda/PDFExtractor.zip",
    "text_translator.zip": "lambda/TextTranslator.zip",
    "status_checker.zip": "lambda/StatusChecker.zip"
}

# ===============================
# 1 Run bundle_lambdas.py
# ===============================
print("🧩 Bundling all Lambda functions...")
subprocess.run(["python", "bundle_lambdas.py"], check=True)


# ===============================
# 2 Deploy CloudFormation stack
# ===============================
print("Deploying CloudFormation stack...")

subprocess.run([
    "aws", "cloudformation", "deploy",
    "--template-file", TEMPLATE_FILE,
    "--stack-name", STACK_NAME,
    "--capabilities", "CAPABILITY_NAMED_IAM",
    "--region", REGION
], check=True)

print("Deployment complete! Backend updated successfully.")

# ===============================
# 3 Upload .zip files to S3
# ===============================
print(" Uploading Lambda artifacts to S3...")
s3 = boto3.client("s3", region_name=REGION)

for file in os.listdir(ARTIFACTS_DIR):
    if file.endswith(".zip") and file in ZIP_TO_S3KEY:
        file_path = os.path.join(ARTIFACTS_DIR, file)
        s3_key = ZIP_TO_S3KEY[file]
        print(f"Uploading {file} → s3://{S3_BUCKET}/{s3_key}")
        s3.upload_file(file_path, S3_BUCKET, s3_key)

print("All artifacts uploaded successfully.")
