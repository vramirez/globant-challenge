import json
import boto3
import logging

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
connection = None
secrets_manager = boto3.client('secretsmanager')
def lambda_handler(event, context):
    print(context)
    secret_name = "globant_db_admin"
    response = secrets_manager.get_secret_value(SecretId=secret_name)
    secret_data = json.loads(response['SecretString'])
    pass
    
