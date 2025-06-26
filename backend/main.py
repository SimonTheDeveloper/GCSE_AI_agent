import os
from typing import List
from uuid import uuid4

import database
import boto3
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, logger
from fastapi.middleware.cors import CORSMiddleware
import schemas
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize a session using Amazon DynamoDB
session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

# Initialize DynamoDB resource
dynamodb = session.resource('dynamodb', endpoint_url=os.getenv("DYNAMODB_ENDPOINT_URL"))

# Reference the DynamoDB table
table = dynamodb.Table('student-progress')

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

@app.get("/api/message")
def get_message():
    # For demo, use a fixed key
    response = table.get_item(Key={"student_id": "demo", "subject_topic": "welcome"})
    return {"message": response.get("Item", {}).get("text", "No message found.")}

@app.post("/api/message")
async def set_message(request: Request):
    data = await request.json()
    text = data.get("text")
    logger.info(f"Received text: {text}")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    table.put_item(Item={
        "student_id": "demo",
        "subject_topic": str(uuid4()),
        "text": text
    })
    return {"status": "ok"}

