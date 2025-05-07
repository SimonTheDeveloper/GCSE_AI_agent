import boto3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize a session using Amazon DynamoDB
session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

# Initialize DynamoDB resource
dynamodb = session.resource('dynamodb')

# Reference the DynamoDB table
table = dynamodb.Table('FlightsTable')

# Scan the table to get all items
response = table.scan()

# Print the items
for item in response['Items']:
    print(item)