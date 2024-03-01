import json
import csv
import boto3
import mysql.connector
import logging
import io
import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS and MySQL clients
s3 = boto3.client('s3')
connection = None
secrets_manager = boto3.client('secretsmanager')
def lambda_handler(event, context):
    db_secret_name = "globant_secret"
    google_secret_name = "google_secret"
    response = secrets_manager.get_secret_value(SecretId=db_secret_name)
    g_response = secrets_manager.get_secret_value(SecretId=google_secret_name)
    db_secret_data = json.loads(response['SecretString'])
    g_secret_data = json.loads(g_response['SecretString'])
    print(fail)
    print(type(fail))
    pass
    try:
        # Retrieve environment variables for MySQL conn
        db_host = db_secret_data['host']
        db_port = db_secret_data['port']
        db_user = db_secret_data['username']
        db_password = db_secret_data['password']
        db_name = db_secret_data['database']

        connect_to_mysql(db_host, db_user, db_password, db_name,db_port)

        # Process files in S3 bucket
        for record in event['Records']:
            bucket_name = record['bucket_name']
            object_key = record['object_key']


            # Read CSV file from S3
            data = read_csv_from_s3(bucket_name, object_key)

            # Process data in batches and insert into MySQL table
            process_data(data)

    except Exception as e:
        logger.error(f"Error processing S3 file: {str(e)}")
        raise

    finally:
        # Close MySQL connection
        if connection is not None:
            connection.close()

def connect_to_mysql(db_host, db_user, db_password, db_name,db_port):
    global connection
    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=db_port
    )

def read_csv_from_s3(bucket_name, file_key):
    """
    Reads a CSV file from an Amazon S3 bucket.
    
    Parameters:
    - bucket_name: The name of the S3 bucket.
    - file_key: The key (path) of the CSV file within the bucket.
    
    Returns:
    - A list of dictionaries representing the CSV data.
    """
    # Initialize S3 client
    s3 = boto3.client('s3')

    # Read CSV file from S3
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        csv_data = response['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error reading CSV file from S3: {e}")
        return []

    # Parse CSV data
    csv_records = []
    csv_reader = csv.DictReader(StringIO(csv_data))
    for row in csv_reader:
        csv_records.append(row)

    return csv_records


def read_google_drive_file(google_secret,file_id):
    # Set up Google credentials
    project_id=google_secret['project_id']
    client_id=google_secret['client_id']
    auth_uri=google_secret['auth_uri']
    token_uri=google_secret['token_uri']
    auth_provider_x509_cert_url=google_secret['auth_provider_x509_cert_url']
    client_secret=google_secret['client_secret']
    private_key_id=google_secret['private_key_id']
    private_key=google_secret['private_key']
    client_email=google_secret['client_email']
    client_x509_cert_url=google_secret['client_x509_cert_url']
    credentials = service_account.Credentials.from_service_account_info(
        {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": private_key_id,
        "private_key": private_key,
        "client_email": client_email,
        "client_id": client_id,
        "client_secret":client_secret,
        "auth_uri": auth_uri,
        "token_uri": token_uri,
        "auth_provider_x509_cert_url": auth_provider_x509_cert_url,
        "client_x509_cert_url": client_x509_cert_url,
        "universe_domain": "googleapis.com",
        }
    )

    # Build the G-Drive service
    service = build('drive', 'v3', credentials=credentials)

    # Download the file content
    request = service.files().get_media(fileId=file_id)
    file_handle = io.BytesIO()
    downloader = MediaIoBaseDownload(file_handle, request)

    done = False
    while done is False:
        status, done = downloader.next_chunk()

    file_content = file_handle.getvalue().decode('utf-8')
    return file_content

def process_data(data,batch_size=1):
    cursor = connection.cursor()
    try:
        batch = []

        for row in data:
            batch.append(row)

            if len(batch) >= batch_size:
                insert_data_into_mysql(cursor, batch)
                batch = []

        # Insert any remaining rows
        if batch:
            insert_data_into_mysql(cursor, batch)

        connection.commit()

    except Exception as e:
        logger.error(f"Error processing csv batch: {str(e)}")
        raise

    finally:
        cursor.close()

def insert_data_into_mysql(table_name,cursor, batch):
    try:
        sql = f"INSERT INTO {table_name}  VALUES (%s, %s)"
        cursor.executemany(sql, batch)
    except Exception as e:
        logger.error(f"Error inserting into MySQL: {str(e)}")
