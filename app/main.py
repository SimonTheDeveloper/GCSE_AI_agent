import os
from typing import List

from . import database
import boto3
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import schemas

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

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/flights/", response_model=List[schemas.Flight])
async def read_flights():
    response = table.scan()
    return response['Items']