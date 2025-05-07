import boto3
import os
from dotenv import load_dotenv
from datetime import date
from flight_data_generator import flight_data
import uuid

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

if __name__ == "__main__":
    flights = flight_data(
        source="London",
        sink="Amsterdam",
        departure_date=date(2024, 10, 3),
        return_date=date(2024, 10, 10),
    )

    # Convert datetime objects to strings and add flight_id
    for flight in flights:
        flight['departure_dt'] = flight['departure_dt'].isoformat()
        flight['arrival_dt'] = flight['arrival_dt'].isoformat()
        flight['flight_id'] = str(uuid.uuid4())
        table.put_item(Item=flight)

    print("Data loaded successfully.")